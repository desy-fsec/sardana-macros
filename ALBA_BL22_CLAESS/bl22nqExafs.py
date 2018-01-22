from sardana.macroserver.macro import Type, Macro, Hookable
from sardana.macroserver.scan import CTScan, MoveableDesc
from sardana.macroserver.macros.scan import getCallable, UNCONSTRAINED
import taurus
import PyTango
from sardana.util.tree import BranchNode

PMAC_REGISTERS = {'MotorDir': 4080, 'StartBuffer': 4081, 'RunProgram': 4082,
                  'NrTriggers': 4083, 'Index': 4084, 'StartPos': 4085,
                  'PulseWidth': 4086, 'AutoInc': 4087}


EV2REVA = 0.2624682843
c = 299792458
h = 4.13566727*10**(-15)
aSi = 5.43102088*10**(-10) # Simo macro su spec
overflow_pmac = 8388608


# TODO: remove starts
def _calculate_positions(moveable_node, start, end):
    '''Function to calculate starting and ending positions on the physical
    motors level.
    :param moveable_node: (BaseNode) node representing a moveable.
                          Can be a BranchNode representing a PseudoMotor,
                          or a LeafNode representing a PhysicalMotor).
    :param start: (float) starting position of the moveable
    :param end: (float) ending position of the moveable

    :return: (list<(float,float)>) a list of tuples comprising starting
             and ending positions. List order is important and preserved.'''
    start_positions = []
    end_positions = []
    if isinstance(moveable_node, BranchNode):
        pseudo_node = moveable_node
        moveable = pseudo_node.data
        moveable_nodes = moveable_node.children
        starts = moveable.calcPhysical(start)
        ends = moveable.calcPhysical(end)
        for moveable_node, start, end in zip(moveable_nodes, starts,
                                             ends):
            _start_positions, _end_positions = _calculate_positions(
                moveable_node,
                start, end)
            start_positions += _start_positions
            end_positions += _end_positions
    else:
        start_positions = [start]
        end_positions = [end]

    return start_positions, end_positions


class qExafsc(Macro, Hookable):
    """
    New version of the qExafs Macro
    """

    env = ('ContScanMG',)

    mem_overload = 1000000
    min_itime = 0.005
    energy_name = "energy"
    bragg_name = "oh_dcm_bragg"
    perp_name = 'oh_dcm_perp'
    pmac_name = 'pmac'
    pmac_ctrl_name = 'controller/dcmturbopmaccontroller/dcm_pmac_ctrl'
    ni_trigger_name = 'triggergate/ni_tg_ctrl/1'

    hints = {}

    param_def = [["startPos", Type.Float, None, "Starting position"],
                 ["end_triggers", [
                     ["endPos", Type.Float, None, "Ending pos value"],
                     ["nrIntervals", Type.Integer, None, "Nr of triggers"],
                     {'min': 1}], None, 'List of [end_pos, triggers] for the '
                                        'region'],
                 ["intTime", Type.Float, None, "Integration time per point"],

                 ["waitFE", Type.Boolean, True, ("Active the waiting for "
                                                 "opening of Front End")],

                 ["configPID", Type.Boolean, True, ("Active the configuration"
                                                    " of the bragg PID ")]]

    def _check_parameters(self, nr_of_triggers):
        if self.integ_time < self.min_itime:
            raise Exception(('You must use a higher integration time.'
                             'The minimum value is %r' % self.min_itime))

        mem = nr_of_triggers**2 * self.integ_time
        if mem > self.mem_overload:
            msg = 'You can not send this scan, because there is not enough ' \
                  'memory,  {0} are too many triggers'. format(nr_of_triggers)
            raise ValueError(msg)

    def _prepare_bragg(self, final_pos):
        self.debug('Preparing Bragg and Perp motors...')

        # TODO verify calculation of the start position on gscan
        # We need to move relative the bragg to solve the problem.

        if self.config_pid:
            self.setPID('new')

        # Configure motor protection Sardana Bug
        if final_pos is None:
            self.macro.warning('CTScan is not prepared to protect '
                               ' the DCM movement!!!')
            return

        bragg_offset = self.bragg['offset'].value
        bragg_sign = self.bragg['sign'].value
        perp_offset = self.perp['offset'].value
        perp_sign = self.perp['sign'].value

        bragg_final, perp_final = final_pos
        bragg_dial = bragg_sign * bragg_final - bragg_offset
        perp_dial = perp_sign * perp_final - perp_offset

        self.pmac_ctrl['NextPosition'] = [bragg_dial, perp_dial]
        self.pmac_ctrl['UseqExafs'] = True

    def _prepare_trigger(self, slave=False):
        self.debug('Configuring NI6602 Trigger...')
        # Configure the Ni660XTrigger
        ni_state = self.ni_trigger.state()
        if ni_state != PyTango.DevState.ON:
            self.ni_trigger.stop()
        self.ni_trigger['slave'] = slave
        self.ni_trigger['retriggerable'] = False

    def _prepare_plc0(self):
        self.debug('Configuring Pmac...')

        # Configure the start trigger from the pmac. This should be moved to
        # the pmac trigger controller.
        bragg_spu = self.bragg['step_per_unit'].value
        bragg_offset = self.bragg['offset'].value
        bragg_pos = float(self.pmac.SendCtrlChar("P").split()[0])
        bragg_enc = float(self.pmac.GetMVariable(101))

        # TODO: Use synchronization
        th1 = self.energy.CalcAllPhysical([self.starts[0]])[0]
        offset_counts = bragg_pos - bragg_enc + (bragg_offset * bragg_spu)

        start_enc = (th1 * bragg_spu) - offset_counts
        if start_enc > overflow_pmac:
            start_enc = start_enc - 2 * overflow_pmac
        elif start_enc < -overflow_pmac:
            start_enc = start_enc + 2 * overflow_pmac

        self.pmac.SetPVariable([PMAC_REGISTERS['MotorDir'],
                                long(self.direction)])
        self.pmac.SetPVariable([PMAC_REGISTERS['StartPos'], long(start_enc)])

    def _post_configure_hook(self):
        self._gScan._index_offset = self.point_id

    def _pre_start_hook(self, final_pos=None):
        self._prepare_bragg(final_pos)
        self._prepare_plc0()

    def _post_move_hook(self):
        self.setPID('old')

    def _post_cleanup_hook(self):
        self._prepare_trigger(slave=False)
        self.restorePmac()
        self._flg_cleanup = True

    def prepare(self, start_pos, ends_intervals_list, int_time, wait_fe,
                config_pid, **opts):

        self.start_pos = start_pos
        self.ends_intervals_list = ends_intervals_list
        self.integ_time = int_time
        self.wait_fe = wait_fe
        self.config_pid = config_pid

        # checking values of the scan
        self.info('Checking parameters....')
        for end_trigger in ends_intervals_list:
            _, nr_of_triggers = end_trigger
            self._check_parameters(nr_of_triggers)

        if self.wait_fe:
            try:
                self.waitFE()
            except Exception as e:
                raise RuntimeError( 'There was an exception with the waitFE '
                                    'macro: %s' % e)

        self.pmac = taurus.Device(self.pmac_name)
        self.pmac_ctrl = taurus.Device(self.pmac_ctrl_name)
        self.perp = taurus.Device(self.perp_name)
        self.bragg = taurus.Device(self.bragg_name)
        self.ni_trigger = taurus.Device(self.ni_trigger_name)
        self.energy = taurus.Device(self.energy_name)

        self.direction = start_pos > ends_intervals_list[0][0]

        self._flg_cleanup = False

        self.nr_interv = ends_intervals_list[0][1]
        self.nr_points = self.nr_interv + 1

        motor = self.getMoveable(self.energy_name)
        self.motors = [motor]

        moveables = [MoveableDesc(moveable=motor)]
        moveables[0].is_reference = True

        self.name = opts.get('name', 'qExafsc')
        env = opts.get('env', {})
        mg_name = self.getEnv('ActiveMntGrp')
        mg = self.getMeasurementGroup(mg_name)
        mg_latency_time = mg.getLatencyTime()

        self.latency_time = mg_latency_time

        constrains = [getCallable(cns) for cns in opts.get('constrains',
                                                           [UNCONSTRAINED])]

        extrainfodesc = opts.get('extrainfodesc', [])

        self._gScan = CTScan(self, self._generator, moveables, env, constrains,
                             extrainfodesc)

        self.setData(self._gScan.data)
        self.hooks = [(self._pre_start_hook, ["pre-start"]),
                      (self._post_move_hook, ["post-move"]),
                      (self._post_configure_hook, ["post-configuration"]),
                      (self._post_cleanup_hook, ["post-cleanup"])]

        self._prepare_trigger(slave=True)

    def _generator(self):
        moveables_trees = self._gScan.get_moveables_trees()
        step = {}

        step["pre-move-hooks"] = self.getHooks('pre-move')
        post_move_hooks = self.getHooks(
            'post-move') + [self._fill_missing_records]
        step["post-move-hooks"] = post_move_hooks
        step["check_func"] = []


        self.waypoints = []
        starts_points = []
        intervals_list = []
        for end_pos, intervals in self.ends_intervals_list:
            starts_points.append(self.start_pos)
            self.waypoints.append(end_pos)
            intervals_list.append(intervals)
            self.start_pos = end_pos

        for i, waypoint in enumerate(self.waypoints):
            self.nr_interv = intervals_list[i]
            self.nr_points = self.nr_interv + 1
            step["active_time"] = self.nr_points * (self.integ_time +
                                                    self.latency_time)

            if i > 0:
                self.point_id += intervals_list[i-1] + 1
            else:
                self.point_id = 0

            step["waypoint_id"] = i
            self.starts = [starts_points[i]]
            self.finals = [waypoint]
            step["positions"] = []
            step["start_positions"] = []

            for start, end, moveable_tree in zip(self.starts, self.finals,
                                                 moveables_trees):
                moveable_root = moveable_tree.root()
                start_positions, end_positions = _calculate_positions(
                    moveable_root, start, end)
                # TODO: move 0.005 more
                step["start_positions"] += start_positions
                step["positions"] += end_positions

            yield step

    def run(self, *args):
        try:
            for step in self._gScan.step_scan():
                yield step
        except Exception:
            pass
        finally:
            if not self._flg_cleanup:
                self._post_cleanup_hook()

    def getTimeEstimation(self):
        return 0.0

    def getIntervalEstimation(self):
        return self.nr_interv

    def _fill_missing_records(self):
        # fill record list with dummy records for the final padding
        nb_of_points = self.nr_points
        scan = self._gScan
        nb_of_total_records = len(scan.data.records)
        nb_of_records = nb_of_total_records - self.point_id
        missing_records = nb_of_points - nb_of_records
        scan.data.initRecords(missing_records)


