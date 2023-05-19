import ujson
from usr.umodbus.rtu import RTU as ModbusRTUMaster
from usr.modules.logging import getLogger

log = getLogger(__name__)


class ModbusAdapter(object):
    def __init__(self):
        super().__init__()
        self.host = ModbusRTUMaster(None)
        log.info('modbus adapter init success')

    def add_channel(self, channel):
        self.host.update_channel(channel)

    def read_coils(self, data):
        """READ COILS slave_addr, coil_address, coil_qty"""
        # data: {"slave": <slave_addr>, "startAddress": <starting_addr>, "quantity": <coil_qty>}
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['quantity']))
        coil_status = self.host.read_coils(data['slave'], data['startAddress'], data['quantity'])
        log.info('Status of coil coil_status: {}'.format(coil_status[data['quantity']]))
        return self.dumps(data, coil_status[:data['quantity']])

    def write_single_coil(self, data):
        # WRITE COILS slave_addr, coil_address, new_coil_val
        # data: {"slave": <slave_addr>, "startAddress": <starting_addr>, "value": <0 or 0xFF00>}
        log.info('slave_addr={}, hreg_address={}, value={}'.format(data['slave'], data['startAddress'], data['value']))
        operation_status = self.host.write_single_coil(data['slave'], data['startAddress'], data['value'])
        log.info('Result of setting coil operation_status: {}'.format(operation_status))
        return operation_status

    def write_multiple_coils(self, data):
        # data: {"slave": <slave_addr>, "startAddress": <starting_addr>, "value": [0, 0, 0xFF00...]}
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['value']))
        operation_status = self.host.write_multiple_coils(data['slave'], data['startAddress'], data['value'])
        log.info('Status of ireg operation_status: {}'.format(operation_status))
        return operation_status

    def read_hoding_registers(self, data):
        # READ HREGS
        # data: {"slave": <slave_addr>, "startAddress": <starting_addr>, "quantity": <register_qty>}
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['quantity']))
        register_value = self.host.read_holding_registers(data['slave'], data['startAddress'], data['quantity'], signed=False)
        log.info('Status of hreg value: {}'.format(register_value))
        return self.dumps(data, register_value)

    def write_single_register(self, data):
        # WRITE HREGS
        # data: {"slave": <slave_addr>, "startAddress": <starting_addr>, "value": <new_hreg_val>}
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['value']))
        operation_status = self.host.write_single_register(data['slave'], data['startAddress'], data['value'], signed=False)
        log.info('Result of setting operation_status: {}'.format(operation_status))
        return operation_status

    def write_multiple_registers(self, data):
        # data: {"slave": <slave_addr>, "startAddress": <starting_addr>, "value": [<new_hreg_val>...]}
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['value']))
        operation_status = self.host.write_multiple_registers(data['slave'], data['startAddress'], data['value'], signed=False)
        log.info('Status of ireg operation_status: {}'.format(operation_status))
        return operation_status

    def read_discrete_inputs(self, data):
        # READ ISTS
        # data: {"slave": <slave_addr>, "startAddress": <starting_addr>, "quantity": <input_qty>}
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['quantity']))
        input_status = self.host.read_discrete_inputs(data['slave'], data['startAddress'], data['quantity'])
        log.info('Status of ist input_status: {}'.format(input_status[:data['quantity']]))
        return self.dumps(data, input_status[:data['quantity']])

    def read_input_registers(self, data):
        # READ IREGS
        # data: {"slave": <slave_addr>, "startAddress": <starting_addr>, "quantity": <register_qty>}
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['quantity']))
        register_value = self.host.read_input_registers(data['slave'], data['startAddress'], data['quantity'], signed=False)
        log.info('Status of ireg register_value: {}'.format(register_value))
        return self.dumps(data, register_value)

    def dumps(self, data, value):
        data.update({'value': list(value)})
        return ujson.dumps(data)
