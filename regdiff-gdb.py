
import gdb
import re

class RegDiff(gdb.Command):
    """Display only registers that have changed since last call."""

    def __init__(self):
        super(RegDiff, self).__init__("reg-diff", gdb.COMMAND_DATA)
        self.last_registers = {}
        self.group_reg = (None, self.fetch_register_list('general'))

    # Thanks to gdb-dashboard:
    # https://github.com/cyrus-and/gdb-dashboard/blob/616ed5100d3588bb70e3b86737ac0609ce0635cc/.gdbinit#L2095
    def fetch_register_list(self, *match_groups):
        """Fetch register names using maintenance print register-groups."""
        names = []
        output = gdb.execute("maintenance print register-groups",
                             to_string=True)

        for line in output.split('\n'):
            fields = line.split()
            if len(fields) != 7:
                continue
            name, _, _, _, _, _, groups = fields
            if not re.match(r'^\w+$', name):
                continue
            if name in match_groups:
                names.append(name)
            for group in groups.split(','):
                if group in match_groups:
                    names.append(name)
                    break
        return names

    def get_register_value(self, name):
        """Get the value of a single register."""
        try:
            return gdb.parse_and_eval(f"${name}")
        except gdb.error:
            return None

    def invoke(self, arg, from_tty):
        """Compare current register values with previous ones."""
        current_registers = {}

        # Get current values for all registers
        for reg in self.group_reg[1]:
            value = self.get_register_value(reg)
            if value is not None:
                current_registers[reg] = str(value)

        # Find changed registers
        changed = {}
        for reg, value in current_registers.items():
            if reg not in self.last_registers or self.last_registers[reg] != value:
                changed[reg] = (self.last_registers.get(reg, '<unknown>'), value)

        self.last_registers = current_registers

        if changed:
            print("Changed registers:")
            max_name_len = max(len(reg) for reg in changed.keys())
            for reg, (old_val, new_val) in sorted(changed.items()):
                print(f"{reg.ljust(max_name_len)} {old_val} -> {new_val}")
        else:
            print("No registers changed since last call.")


RegDiff()
