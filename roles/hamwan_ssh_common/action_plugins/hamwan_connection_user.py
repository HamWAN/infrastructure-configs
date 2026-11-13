"""Report the user name Ansible is actually using to log in to the current host.

Shared by routeros_common and users (roles/hamwan_ssh_common).

This runs on the controller only; it sends nothing to the device.  It exists because the user
name can come from several places - ansible_user in inventory, -u on the command line,
remote_user in ansible.cfg, $ANSIBLE_REMOTE_USER - and only some of those are visible as
variables.  A '-u myname+cet512w' on the command line, for example, never appears as
ansible_user.  Ansible resolves all of them into the connection's remote_user, which is what
this returns.

Returns:
  user    the login name, exactly as Ansible will use it (may include a '+options' suffix);
          empty if Ansible has not settled on one (it would then fall back to ssh's default)
  source  where it was read from: 'connection' or 'play_context'
"""
from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    # Nothing is sent to the host, so no connection is needed.  Saying so matters for persistent
    # connections (network_cli): without it Ansible starts the connection process for this task,
    # with a fresh idle timer that can run out just as the next command arrives ("Unable to
    # connect to socket").  For those connections the name then comes from the play context.
    TRANSFERS_FILES = False
    _requires_connection = False

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        user, source = None, None
        try:
            user = self._connection.get_option("remote_user")
            source = "connection"
        except Exception:  # noqa: BLE001 - not every connection plugin has the option
            user = None
        if not user:
            user = getattr(self._play_context, "remote_user", None)
            source = "play_context"
        result.update(changed=False, user=user or "", source=source if user else None)
        return result
