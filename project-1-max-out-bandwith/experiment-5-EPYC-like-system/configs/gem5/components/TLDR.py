from gem5.components.cachehierarchies.ruby.abstract_ruby_cache_hierarchy import AbstractRubyCacheHierarchy
from gem5.components.cachehierarchies.abstract_three_level_cache_hierarchy import (
    AbstractThreeLevelCacheHierarchy,
)
from gem5.coherence_protocol import CoherenceProtocol
from gem5.isas import ISA
from gem5.components.boards.abstract_board import AbstractBoard
from gem5.utils.requires import requires

from gem5.components.cachehierarchies.ruby.caches.mesi_three_level.dma_controller import DMAController

from m5.objects import RubySystem, DMASequencer, RubyPortProxy, SimpleNetwork

from .core_complex import CoreComplex

class TLDRCache(AbstractRubyCacheHierarchy, AbstractThreeLevelCacheHierarchy):
    def __init__(
        self,
        l1i_size: str,
        l1i_assoc: int,
        l1d_size: str,
        l1d_assoc: int,
        l2_size: str,
        l2_assoc: int,
        l3_size: str,
        l3_assoc: int,
        num_core_complexes: int,
    ):
        AbstractRubyCacheHierarchy.__init__(self=self)
        AbstractThreeLevelCacheHierarchy.__init__(
            self=self,
            l1i_size=l1i_size,
            l1i_assoc=l1i_assoc,
            l1d_size=l1d_size,
            l1d_assoc=l1d_assoc,
            l2_size=l2_size,
            l2_assoc=l2_assoc,
            l3_size=l3_size,
            l3_assoc=l3_assoc,
        )

        self._l1_controllers = []
        self._l2_controllers = []
        self._l3_controllers = []
        self._directory_controllers = []
        self._dma_controllers = []
        self._core_complexes = []
        self._num_core_complexes = num_core_complexes

    def incorporate_cache(self, board: AbstractBoard) -> None:

        requires(
            coherence_protocol_required=CoherenceProtocol.MESI_THREE_LEVEL
        )

        cache_line_size = board.get_cache_line_size()

        self.ruby_system = RubySystem()

        # MESI_Three_Level needs 3 virtual networks
        self.ruby_system.number_of_virtual_networks = 3

        self.ruby_system.network = SimpleNetwork()
        self.ruby_system.network.netifs = []
        self.ruby_system.network.ruby_system = self.ruby_system
        self.ruby_system.network.number_of_virtual_networks = 3

        self._create_dma_controller(board, self.ruby_system)

        # SimpleNetwork requires .int_links, .ext_links, and .routers to exist
        # if we want to call SimpleNetwork.setup_buffers().
        # We will create the links and the routers when setting up the core complex.
        self.ruby_system.network._int_links = []
        self.ruby_system.network._ext_links = []
        self.ruby_system.network._routers = []

        # Setting up the core complex
        all_cores = board.get_processor().get_cores()
        num_cores_per_core_complex = len(all_cores) // self._num_core_complexes

        self.core_complexes = [CoreComplex(
                board = board,
                cores = all_cores[core_complex_idx*num_cores_per_core_complex:(core_complex_idx + 1) * num_cores_per_core_complex],
                addr_range = address_range,
                ruby_system = self.ruby_system,
                network = self.ruby_system.network,
                mem_port = mem_port,
                l1i_size = self._l1i_size,
                l1i_assoc = self._l1i_assoc,
                l1d_size = self._l1d_size,
                l1d_assoc = self._l1d_assoc,
                l2_size = self._l2_size,
                l2_assoc = self._l2_assoc,
                l3_size = self._l3_size,
                l3_assoc = self._l3_assoc,
        ) for core_complex_idx, (address_range, mem_port) in enumerate(board.get_mem_ports())]

        self.ruby_system.num_of_sequencers = len(all_cores) + len(self._dma_controllers)
        # SimpleNetwork requires .int_links and .routers to exist
        # if we want to call SimpleNetwork.setup_buffers()
        self.ruby_system.network.int_links = self.ruby_system.network._int_links
        self.ruby_system.network.ext_links = self.ruby_system.network._ext_links
        self.ruby_system.network.routers = self.ruby_system.network._routers
        self.ruby_system.network.setup_buffers()

        # Set up a proxy port for the system_port. Used for load binaries and
        # other functional-only things.
        self.ruby_system.sys_port_proxy = RubyPortProxy()
        board.connect_system_port(self.ruby_system.sys_port_proxy.in_ports)

        from pprint import pprint
        pprint(vars(self.ruby_system))
        pprint(vars(self.ruby_system.network))

    def _create_dma_controller(self, board, ruby_system):
        self._dma_controllers = []
        if board.has_dma_ports():
            dma_ports = board.get_dma_ports()
            for i, port in enumerate(dma_ports):
                ctrl = DMAController(self.ruby_system.network, cache_line_size)
                ctrl.dma_sequencer = DMASequencer(version=i, in_ports=port)
                self._dma_controllers.append(ctrl)
                ctrl.ruby_system = self.ruby_system
            ruby_system.dma_controllers = self._dma_controllers
