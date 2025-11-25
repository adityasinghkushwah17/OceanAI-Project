import requests, time, sys

BASE = 'http://localhost:8000'

def p(msg):
    print('> ' + msg)

def main():
    t = str(int(time.time()))
    email = f'smoke_{t}@example.com'
    password = 'TestPass123!'

    p('Registering user')
    r = requests.post(BASE + '/auth/register', json={'email': email, 'password': password})
    if r.status_code not in (200,201):
        print('Register failed', r.status_code, r.text); sys.exit(1)
    token = r.json()['access_token']
    headers = {'Authorization': 'Bearer ' + token}

    p('Creating project')
    proj_body = {'title': 'Smoke Test Project', 'doc_type': 'docx', 'prompt': 'A market analysis of the EV industry in 2025', 'sections': []}
    r = requests.post(BASE + '/projects', json=proj_body, headers=headers)
    if r.status_code != 200:
        print('Create project failed', r.status_code, r.text); sys.exit(1)
    proj = r.json()
    pid = proj['id']
    p(f'Project created id={pid}')

    p('Requesting AI-suggested outline')
    r = requests.post(BASE + f'/projects/{pid}/suggest_outline?count=3', headers=headers)
    if r.status_code != 200:
        print('Suggest outline failed', r.status_code, r.text); sys.exit(1)
    suggestions = r.json().get('suggestions', [])
    p('Suggestions: ' + str(suggestions))

    if suggestions:
        p('Applying outline')
        r = requests.post(BASE + f'/projects/{pid}/apply_outline', json={'titles': suggestions}, headers=headers)
        if r.status_code != 200:
            print('Apply outline failed', r.status_code, r.text); sys.exit(1)
        p('Applied outline')
    else:
        p('No suggestions received')

    p('Triggering generation')
    r = requests.post(BASE + f'/projects/{pid}/generate', headers=headers)
    if r.status_code != 200:
        print('Generate failed', r.status_code, r.text); sys.exit(1)
    p('Generation completed')

    p('Exporting document')
    r = requests.get(BASE + f'/export/{pid}', headers=headers)
    if r.status_code != 200:
        print('Export failed', r.status_code, r.text); sys.exit(1)
    fname = f'smoke_export_{pid}.docx'
    with open(fname, 'wb') as f:
        f.write(r.content)
    p('Export saved to ' + fname)

if __name__ == '__main__':
    main()
