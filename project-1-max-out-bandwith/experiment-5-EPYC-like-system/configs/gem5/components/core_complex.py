from typing import List, Tuple

from gem5.isas import ISA
from gem5.components.boards.abstract_board import AbstractBoard
from gem5.components.processors.abstract_core import AbstractCore
from gem5.components.cachehierarchies.abstract_three_level_cache_hierarchy import (
    AbstractThreeLevelCacheHierarchy,
)
from gem5.components.cachehierarchies.ruby.caches.mesi_three_level.l1_cache import L1Cache
from gem5.components.cachehierarchies.ruby.caches.mesi_three_level.l2_cache import L2Cache
from gem5.components.cachehierarchies.ruby.caches.mesi_three_level.l3_cache import L3Cache
from gem5.components.cachehierarchies.ruby.caches.mesi_three_level.directory import Directory

from m5.objects import SubSystem, L2Cache_Controller, AddrRange, RubySequencer, Switch, SimpleIntLink, SimpleExtLink, SubSystem, SimObject

#from .router import Router
#from .ruby_link import ExtLink, IntLink

class CoreComplex(SubSystem):
    _core_id = 0
    _core_complex_id = 0
    _int_link_id = 0
    _ext_link_id = 0
    _router_id = 0

    @classmethod
    def _get_core_id(cls):
        cls._core_id += 1
        return cls._core_id - 1

    @classmethod
    def _get_core_complex_id(cls):
        cls._core_complex_id += 1
        return cls._core_complex_id - 1

    @classmethod
    def _get_int_link_id(cls):
        cls._int_link_id += 1
        return cls._int_link_id - 1

    @classmethod
    def _get_ext_link_id(cls):
        cls._ext_link_id += 1
        return cls._ext_link_id - 1

    @classmethod
    def _get_router_id(cls):
        cls._router_id += 1
        return cls._router_id - 1

    def __init__(
        self,
        board: AbstractBoard,
        cores: List[AbstractCore],
        addr_range: AddrRange,
        ruby_system,
        network,
        mem_port,
        l1i_size: str,
        l1i_assoc: int,
        l1d_size: str,
        l1d_assoc: int,
        l2_size: str,
        l2_assoc: int,
        l3_size: str,
        l3_assoc: int,
    ):
        super().__init__()

        self._l1i_size = l1i_size
        self._l1i_assoc = l1i_assoc
        self._l1d_size = l1d_size
        self._l1d_assoc = l1d_assoc
        self._l2_size = l2_size
        self._l2_assoc = l2_assoc
        self._l3_size = l3_size
        self._l3_assoc = l3_assoc
        
        self._board = board
        self._cores = cores
        self._addr_range = addr_range
        self._ruby_system = ruby_system
        self._network = network
        self._mem_port = mem_port
        self._cache_line_size = 64

        self._l1_controllers = []
        self._l2_controllers = []
        self._l3_controllers = []
        self._directory_controllers = []

        self._core_complex_id = self._get_core_complex_id()
        self._int_routers = []
        self._core_complex_router = None # this will be connect to component outside the core complex
        self._int_links = []
        self._ext_links = []

        self._create_core_complex()

    def get_directory_controllers(self):
        return self._directory_controllers
    def get_int_links(self):
        return self._int_links
    def get_ext_links(self):
        return self._ext_links
    def get_all_routers(self):
        return [*self._int_routers, self._core_complex_router]

    def _create_core_complex(self):
        # Create the controllers and link the L1 and its corresponding L2
        self.core_clusters = [self._create_core_private_cache(core) for core in self._cores]
        self._create_core_complex_shared_cache()
        self._create_core_complex_directory_controller()

        # Setting up a router and an external link for each controller
        self._create_external_links()
        # Setting up a router for this core complex that is connected to
        # all other routers in the core complex via internal links.
        self._create_internal_links()

        # we can call SimpleNetwork.setup_buffers() later.
        self._network._int_links.extend(self.get_int_links())
        self._network._ext_links.extend(self.get_ext_links())
        self._network._routers.extend(self.get_all_routers())

    def _create_core_private_cache(self, core: AbstractCore):
        cluster = SubSystem()
        core_id = self._get_core_id()

        cluster.l1_cache = L1Cache(
            l1i_size = self._l1i_size,
            l1i_assoc = self._l1i_assoc,
            l1d_size = self._l1d_size,
            l1d_assoc = self._l1d_assoc,
            network = self._network,
            core = core,
            cache_line_size = self._cache_line_size,
            target_isa = self._board.processor.get_isa(),
            clk_domain = self._board.get_clock_domain(),
        )
        cluster.l1_cache.sequencer = RubySequencer(
            version = core_id,
            dcache = cluster.l1_cache.Dcache,
            clk_domain = cluster.l1_cache.clk_domain
        )
        if self._board.has_io_bus():
            cluster.l1_cache.sequencer.connectIOPorts(self._board.get_io_bus())
        cluster.l1_cache.ruby_system = self._ruby_system
        core.connect_icache(cluster.l1_cache.sequencer.in_ports)
        core.connect_dcache(cluster.l1_cache.sequencer.in_ports)
        core.connect_walker_ports(
            cluster.l1_cache.sequencer.in_ports, cluster.l1_cache.sequencer.in_ports
        )
        if self._board.get_processor().get_isa() == ISA.X86:
            core.connect_interrupt(
                cluster.l1_cache.sequencer.interrupt_out_port,
                cluster.l1_cache.sequencer.in_ports
            )
        else:
            core.connect_interrupt()
        self._l1_controllers.append(cluster.l1_cache)

        cluster.l2_cache = L2Cache(
            l2_size=self._l2_size,
            l2_assoc=self._l2_assoc,
            network=self._network,
            core=core,
            num_l3Caches=1, # each core complex has 1 slice of L3 Cache
            cache_line_size=self._cache_line_size,
            cluster_id=self._core_complex_id,
            target_isa=self._board.processor.get_isa(),
            clk_domain=self._board.get_clock_domain(),
        )
        cluster.l2_cache.ruby_system = self._ruby_system
        self._l2_controllers.append(cluster.l2_cache)
        # L0Cache in the ruby backend is l1 cache in stdlib
        # L1Cache in the ruby backend is l2 cache in stdlib
        cluster.l2_cache.bufferFromL0 = cluster.l1_cache.bufferToL1
        cluster.l2_cache.bufferToL0 = cluster.l1_cache.bufferFromL1
        
        return cluster

    def _create_core_complex_shared_cache(self):
        self.l3_cache = L3Cache(
            l3_size=self._l3_size,
            l3_assoc=self._l3_assoc,
            network=self._network,
            num_l3Caches=1,
            cache_line_size=self._cache_line_size,
            cluster_id=self._core_complex_id,
        )
        self.l3_cache.ruby_system = self._ruby_system

    def _create_core_complex_directory_controller(self):
        directory_controller = Directory(
            self._network, self._cache_line_size, self._addr_range, self._mem_port
        )
        directory_controller.ruby_system = self._ruby_system
        self._directory_controllers.append(directory_controller)

    # This is where all routers and links are created
    def _create_external_links(self):
        for l1_controller in self._l1_controllers:
            router = Switch()
            router.router_id = self._get_router_id()
            ext_link = SimpleExtLink()
            ext_link.link_id = self._get_ext_link_id()
            ext_link.ext_node = l1_controller
            ext_link.int_node = router
            self._int_routers.append(router)
            self._ext_links.append(ext_link)
        for l2_controller in self._l2_controllers:
            router = Switch()
            router.router_id = self._get_router_id()
            ext_link = SimpleExtLink()
            ext_link.link_id = self._get_ext_link_id()
            ext_link.ext_node = l2_controller
            ext_link.int_node = router
            self._int_routers.append(router)
            #self._network._routers.append(router)
            self._ext_links.append(ext_link)

        l3_controller_router = Switch()
        l3_controller_router.router_id = self._get_router_id()
        l3_controller_ext_link = SimpleExtLink()
        l3_controller_ext_link.link_id = self._get_ext_link_id()
        l3_controller_ext_link.ext_node = self.l3_cache
        l3_controller_ext_link.int_node = l3_controller_router
        # Odd stuff
        self._int_routers.append(l3_controller_router)
        #self._network._routers.append(l3_controller_router)
        self._ext_links.append(l3_controller_ext_link)
        
        directory_controller_router = Switch()
        directory_controller_router.router_id = self._get_router_id()
        directory_controller_ext_link = SimpleExtLink()
        directory_controller_ext_link.link_id = self._get_ext_link_id()
        directory_controller_ext_link.ext_node = self._directory_controllers[0]
        directory_controller_ext_link.int_node = directory_controller_router
        # Odd stuff
        self._int_routers.append(directory_controller_router)
        #self._network._routers.append(directory_controller_router)
        self._ext_links.append(directory_controller_ext_link)

    def _create_internal_links(self):
        self._core_complex_router = Switch()
        self._core_complex_router.router_id = self._get_router_id()
        #self._network._routers.append(self._core_complex_router)
        for r in self._int_routers:
            int_link_1 = SimpleIntLink()
            int_link_1.link_id = self._get_int_link_id()
            int_link_1.src_node = self._core_complex_router
            int_link_1.dst_node = r
            int_link_2 = SimpleIntLink()
            int_link_2.link_id = self._get_int_link_id()
            int_link_2.src_node = r
            int_link_2.dst_node = self._core_complex_router
            # Odd stuff
            self._int_links.extend([int_link_1, int_link_2])
            #self._network._int_links.extend([int_link_1, int_link_2]) 
