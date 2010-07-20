import datetime
import model
import re
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
<option value="10">10 seconds</option>
<option value="60">1 minute</option>
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
        tag = re.sub('[^a-zA-Z0-9]', '', self.request.get('tag')).lower()
        if not tag:
            raise utils.ErrorMessage(400, 'Tag had no letters or digits.')
        duration = int(self.request.get('duration'))
        stop_time = datetime.datetime.utcfromtimestamp(time.time() + duration)
        model.Member.join(member.user, tag, stop_time)
        raise utils.Redirect('/view/' + tag)


if __name__ == '__main__':
    utils.run([('/join', Join)])
