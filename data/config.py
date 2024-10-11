from environs import Env
env = Env()
env.read_env()
BOT_TOKEN='7262239509:AAH28O7sehP0a4fXl2u3XvkUvyrxPrtopRI'
# BOT_TOKEN='7262239509:AAGrYsJaL8oEVYqtSVLPibA-g9xnDxj400U'
ADMINS=env.list('ADMINS')
# SEO=env.list('SEO')
SEO = ['147737693', '816660001']