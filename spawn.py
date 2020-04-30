# IMPORT
try:
    from settings import settings
except ModuleNotFoundError:
    raise ModuleNotFoundError(
          'settings.py is missing, check the files are ' +
          'in place or download the repository again\n'
            )
try:
    import advanced.handler
except ModuleNotFoundError:
    raise ModuleNotFoundError(
          'advanced/handler.py is missing, check the files are ' +
          'in place or download the repository again\n'
            )
from os import getcwd

# MAIN
handler = advanced.handler.Handler(settings)
handler.clear()
print('Welcome, Spawn is a simple Python script to automatize the ' +
      'Wasabi mixing process\n'
      )
if handler.status == 'first_run':
    if handler.auto_generate:
        handler.create_password()
    else:
        handler.user_password()
    handler.create_wallet()
    handler.create_addresses()
    handler.stamp_addresses(getcwd())
    handler.close_wasabi()
elif handler.status == 'mixing':
        handler.ask_password()
handler.start_mixing()
handler.print_ui()
