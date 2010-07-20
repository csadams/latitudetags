import datetime
import model
import time
import utils


class Join(utils.Handler):
    def get(self):
        member = self.require_member()
        self.write('''
<p>
<form method="post">
Join <input name="tag" value="#">
for <select name="duration">
<option value="600">10 minutes</option>
<option value="3600">1 hour</option>
<option value="7200">2 hours</option>
<option value="21600">6 hours</option>
<option value="86400">24 hours</option>
<option value="172800">48 hours</option>
</select>.
<p>
<input type="submit"
value="Join this group and share my location with everyone in it">
</form>
        ''')

    def post(self):
        member = self.require_member()
        tag = self.request.get('tag')
        duration = int(self.request.get('duration'))
        stop_time = datetime.datetime.utcfromtimestamp(time.time() + duration)
        model.Member.join(member.user, tag, stop_time)


if __name__ == '__main__':
    utils.run([('/join', Join)])
