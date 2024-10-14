from environs import Env
env = Env()
env.read_env()
BOT_TOKEN='7262239509:AAEAZIPHjBAXIZQ5Nr2cTXgbqUJ_8-BzzXc'
ADMINS=env.list('ADMINS')
# SEO=env.list('SEO')
SEO = ['147737693', '816660001']