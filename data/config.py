from environs import Env
env = Env()
env.read_env()
# BOT_TOKEN='7784958688:AAHB4GfO7YmrNL4kNDIkm7zd1q0n7pYoQkA'
BOT_TOKEN='7409681510:AAGcu6p1411vNiardtcmZUUmUSxij7slXWI'
ADMINS=env.list('ADMINS')
# SEO=env.list('SEO')
SEO = ['147737693', '816660001']