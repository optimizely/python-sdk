class BaseUserProfileService(object):
  def __init__(self, user_profiles):
    self.user_profiles = {profile['user_id']: profile for profile in user_profiles} if user_profiles else {}


class NormalService(BaseUserProfileService):
  def lookup(self, user_id):
    return self.user_profiles.get(user_id)

  def save(self, user_profile):
    user_id = user_profile['user_id']
    self.user_profiles[user_id] = user_profile


class LookupErrorService(NormalService):
  def lookup(self, user_id):
    raise IOError


class SaveErrorService(NormalService):
  def save(self, user_profile):
    raise IOError
