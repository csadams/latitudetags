import utils

class Main(utils.Handler):
    def get(self):
        self.write('''<head><meta name="google-site-verification" content="70w5cEoaURSRVD2iItuAIVm0lN3k4vWzJXfMyT3XgW4" /></head>
        <body></body>
        ''')

if __name__ == '__main__':
    utils.run([('/', Main)])
