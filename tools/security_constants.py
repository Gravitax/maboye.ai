"""
Security Constants

Centralized definition of safe and dangerous shell commands.
Used by BashTool for validation and ToolsCommand for listing.
"""

# Security: Safe commands whitelist
SAFE_SHELL_COMMANDS = {
    'ls', 'pwd', 'echo', 'cat', 'head', 'tail', 'grep', 'find',
    'wc', 'sort', 'uniq', 'diff', 'tree', 'file', 'stat',
    'git', 'npm', 'pip', 'python', 'node', 'cargo', 'go',
    'mkdir', 'cp', 'mv', 'touch', 'chmod', 'chown',
    'which', 'whereis', 'whoami', 'hostname', 'date', 'cal',
    'ps', 'top', 'df', 'du', 'free', 'uname'
}

# Security: Dangerous commands blacklist
DANGEROUS_SHELL_COMMANDS = {
    'rm', 'rmdir', 'dd', 'mkfs', 'fdisk', 'parted',
    'kill', 'killall', 'shutdown', 'reboot', 'halt',
    'sudo', 'su', 'passwd', 'useradd', 'userdel',
    'iptables', 'ufw', 'firewall-cmd',
    'format', 'del', 'deltree'
}
