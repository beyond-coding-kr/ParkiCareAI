import json
from pyscript import window

class Storage:
    BASE_URL = '/api'

    @staticmethod
    def request_sync(endpoint, method='GET', body=None):
        try:
            xhr = window.XMLHttpRequest.new()
            xhr.open(method, Storage.BASE_URL + endpoint, False)
            xhr.setRequestHeader('Content-Type', 'application/json')
            if body:
                xhr.send(json.dumps(body))
            else:
                xhr.send(None)
            
            if 200 <= xhr.status < 300:
                resp = json.loads(xhr.responseText)
                return resp.get('data') if resp.get('ok') else None
        except Exception as e:
            print("XHR Error:", e)
        return None

    @staticmethod
    def get_profiles():
        return Storage.request_sync('/profiles') or []

    @staticmethod
    def save_profile(profile):
        return Storage.request_sync('/profiles', 'POST', profile)

    @staticmethod
    def delete_profile(id):
        return Storage.request_sync(f'/profiles/{id}', 'DELETE')

    @staticmethod
    def get_current_profile():
        id = window.localStorage.getItem('parkicare_current_profile')
        if not id:
            return None
        profiles = Storage.get_profiles()
        for p in profiles:
            if p.get('id') == id:
                return p
        return None

    @staticmethod
    def set_current_profile(id):
        window.localStorage.setItem('parkicare_current_profile', id)

    @staticmethod
    def get_sessions(profile_id, game_type):
        all_sessions = Storage.request_sync(f'/sessions/profile/{profile_id}') or []
        return [s for s in all_sessions if s.get('gameType') == game_type]

    @staticmethod
    def save_session(profile_id, game_type, session_data):
        session_data['profileId'] = profile_id
        session_data['gameType'] = game_type
        return Storage.request_sync('/sessions', 'POST', session_data)

    @staticmethod
    def get_weak_profile(profile_id):
        return Storage.request_sync(f'/analysis/{profile_id}')

    @staticmethod
    def run_analysis(profile_id):
        return Storage.request_sync(f'/analysis/{profile_id}')

    @staticmethod
    def get_problem(game_type, profile_id=None, accessible=True):
        url = f'/generate_problem?gameType={game_type}&accessible={"true" if accessible else "false"}'
        if profile_id:
            url += f'&profileId={profile_id}'
        return Storage.request_sync(url)

    @staticmethod
    def login(username, password):
        res = Storage.request_sync('/auth/login', 'POST', {'username': username, 'password': password})
        if res:
            window.localStorage.setItem('parkicare_user', json.dumps(res))
            return res
        return None

    @staticmethod
    def register(username, password):
        res = Storage.request_sync('/auth/register', 'POST', {'username': username, 'password': password})
        if res:
            window.localStorage.setItem('parkicare_user', json.dumps(res))
            return res
        return None

    @staticmethod
    def logout():
        Storage.request_sync('/auth/logout', 'POST')
        window.localStorage.removeItem('parkicare_user')
        window.localStorage.removeItem('parkicare_current_profile')

    @staticmethod
    def get_current_user():
        user_str = window.localStorage.getItem('parkicare_user')
        if not user_str:
            return None
        try:
            return json.loads(user_str)
        except:
            return None

    @staticmethod
    def check_session():
        res = Storage.request_sync('/auth/me')
        if res:
            window.localStorage.setItem('parkicare_user', json.dumps(res))
            return res
        else:
            window.localStorage.removeItem('parkicare_user')
            return None
