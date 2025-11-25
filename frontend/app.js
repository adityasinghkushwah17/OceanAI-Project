const API = 'http://localhost:8000'
let token = null

// Auth handlers
document.getElementById('btn-register').onclick = async () => authAction('register')
document.getElementById('btn-login').onclick = async () => authAction('login')

async function authAction(mode){
  const email = document.getElementById('email').value
  const password = document.getElementById('password').value
  const res = await fetch(API + '/auth/' + mode, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email,password})})
  const data = await res.json()
  if (res.ok) { token = data.access_token; onLogin(); }
  else alert((data && data.detail) ? data.detail : JSON.stringify(data))
}

async function onLogin(){
  // hide auth inputs (simple UX) and load projects
  document.querySelector('.top-actions .auth-area').style.display = 'none'
  loadProjects()
}

// Create project
document.getElementById('create-proj').onclick = async () => {
  const title = document.getElementById('proj-title').value
  const doc_type = document.getElementById('proj-type').value
  const prompt = document.getElementById('proj-prompt').value
  const body = {title, doc_type, prompt, sections: []}
  const res = await fetch(API + '/projects', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token}, body: JSON.stringify(body)})
  if (res.ok) { loadProjects(); document.getElementById('proj-title').value=''; document.getElementById('proj-prompt').value=''; }
  else alert(JSON.stringify(await res.json()))
}

// Load projects into sidebar
async function loadProjects(){
  const res = await fetch(API + '/projects', {headers:{'Authorization':'Bearer '+token}})
  const projects = await res.json()
  const el = document.getElementById('projects-list')
  el.innerHTML = ''
  projects.forEach(p=>{
    const div = document.createElement('div')
    div.className='project-card'
    div.innerHTML = `<div class="meta"><div class="title">${escapeHtml(p.title)}</div><div class="type">${p.doc_type}</div></div><div class="project-actions"><button class='btn small' onclick="openProject(${p.id})">Open</button><button class='btn small outline' onclick="suggestOutline(${p.id})">AI</button><button class='btn small' onclick="generate(${p.id})">Gen</button><button class='btn small' onclick=\"exportProject(${p.id})\">Export</button></div>`
    el.appendChild(div)
  })
}

// Open project in editor pane
async function openProject(id){
  const res = await fetch(API + '/projects/' + id, {headers:{'Authorization':'Bearer '+token}})
  const p = await res.json()
  const editor = document.getElementById('editor')
  editor.innerHTML = `<div class='header-row'><h2>${escapeHtml(p.title)}</h2><div class='header-actions'><button class='btn outline' onclick="suggestOutline(${p.id})">Suggest Outline</button><button class='btn primary' onclick="generate(${p.id})">Generate</button><button class='btn' onclick=\"exportProject(${p.id})\">Export</button></div></div><div id='sections'></div>`
  const secEl = document.getElementById('sections')
  if (!p.sections || p.sections.length===0){ secEl.innerHTML = '<div class="placeholder">No sections yet — use AI-Suggest or add titles.</div>'; return }
  secEl.innerHTML = ''
  p.sections.forEach(s=>{
    const sdiv = document.createElement('div')
    sdiv.className='section'
    sdiv.id = 'sec-'+s.id
    sdiv.innerHTML = `<h4>${escapeHtml(s.title)}</h4><textarea id='ta-${s.id}'>${escapeHtml(s.content||'')}</textarea><div style="margin-top:8px"><button class='btn small' onclick=\"refine(${s.id})\">Refine</button> <button class='btn small outline' onclick=\"save(${s.id})\">Save</button> <button class='btn small' onclick=\"like(${s.id},true)\">Like</button> <button class='btn small outline' onclick=\"like(${s.id},false)\">Dislike</button></div><div style='margin-top:8px'><input id='cmt-${s.id}' placeholder='Comment' /> <button class='btn small' onclick=\"comment(${s.id})\">Comment</button></div>`
    secEl.appendChild(sdiv)
  })
}

async function generate(id){
  const res = await fetch(API + '/projects/' + id + '/generate', {method:'POST', headers:{'Authorization':'Bearer '+token}})
  if (res.ok) { alert('Generation complete'); openProject(id) }
  else alert(JSON.stringify(await res.json()))
}

async function refine(section_id){
  const instr = prompt('Refinement prompt (e.g., Make this shorter):')
  if (!instr) return
  const res = await fetch(API + '/refine', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token}, body: JSON.stringify({section_id, prompt: instr})})
  const data = await res.json()
  if (res.ok){ document.getElementById('ta-'+section_id).value = data.new_content }
  else alert(JSON.stringify(data))
}

async function save(section_id){
  const val = document.getElementById('ta-'+section_id).value
  const res = await fetch(API + '/refine', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token}, body: JSON.stringify({section_id, prompt: 'save content: '+val})})
  const data = await res.json()
  if (res.ok) alert('Saved')
  else alert(JSON.stringify(data))
}

async function like(section_id, liked){
  // placeholder UX
  const el = document.getElementById('sec-'+section_id)
  el.style.borderColor = liked ? 'rgba(94,234,212,0.6)' : 'rgba(255,80,80,0.2)'
}

async function comment(section_id){
  const text = document.getElementById('cmt-'+section_id).value
  if (!text) return
  const res = await fetch(API + '/comment', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token}, body: JSON.stringify({section_id, text})})
  if (res.ok) alert('Comment saved')
  else alert(JSON.stringify(await res.json()))
}

async function exportProject(id){
  const res = await fetch(API + '/export/' + id, {headers:{'Authorization':'Bearer '+token}})
  if (res.ok){
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `project_${id}`
    document.body.appendChild(a)
    a.click()
    a.remove()
  } else alert(JSON.stringify(await res.json()))
}

// Suggestions UI
let _currentSuggestProject = null
async function suggestOutline(project_id){
  _currentSuggestProject = project_id
  const count = parseInt(prompt('How many sections/slides to suggest?', '5') || '5')
  const res = await fetch(API + '/projects/' + project_id + '/suggest_outline', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token}, body: JSON.stringify({count})})
  const data = await res.json()
  if (!res.ok){ alert(JSON.stringify(data)); return }
  const titles = data.suggestions || []
  openSuggestionsPanel(titles)
}

function openSuggestionsPanel(titles){
  const panel = document.getElementById('suggestions-panel')
  const list = document.getElementById('suggestions-list')
  list.innerHTML = ''
  titles.forEach((t, idx) => {
    const row = document.createElement('div')
    row.className = 'suggestion-item'
    row.innerHTML = `<input id='s-${idx}' value='${escapeHtml(t)}' /> <button class='btn small outline' onclick='removeSuggestion(${idx})'>Remove</button>`
    list.appendChild(row)
  })
  const addRow = document.createElement('div')
  addRow.className = 'suggestion-item'
  addRow.innerHTML = `<input id='s-add' placeholder='Add new title...' /> <button class='btn small' id='add-s-btn'>Add</button>`
  list.appendChild(addRow)
  document.getElementById('apply-suggestions').onclick = applySuggestions
  document.getElementById('close-suggestions').onclick = closeSuggestionsPanel
  document.getElementById('add-s-btn').onclick = () => {
    const v = document.getElementById('s-add').value.trim()
    if (!v) return
    const idx = list.querySelectorAll('.suggestion-item').length - 1
    const row = document.createElement('div')
    row.className = 'suggestion-item'
    row.innerHTML = `<input id='s-${idx}' value='${escapeHtml(v)}' /> <button class='btn small outline' onclick='removeSuggestion(${idx})'>Remove</button>`
    list.insertBefore(row, addRow)
    document.getElementById('s-add').value = ''
  }
  panel.style.display = 'flex'
}

function closeSuggestionsPanel(){ document.getElementById('suggestions-panel').style.display = 'none' }

function removeSuggestion(idx){
  const list = document.getElementById('suggestions-list')
  const items = Array.from(list.querySelectorAll('.suggestion-item'))
  if (idx < items.length - 1){
    items[idx].remove()
    const remain = Array.from(list.querySelectorAll('.suggestion-item'))
    remain.forEach((el, i) => {
      const input = el.querySelector('input')
      if (input) input.id = 's-' + i
      const btn = el.querySelector('button')
      if (btn && btn.textContent.trim() === 'Remove') btn.setAttribute('onclick', `removeSuggestion(${i})`)
    })
  }
}

function escapeHtml(unsafe){
  return (unsafe||'').toString().replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"','&quot;').replaceAll("'","&#039;")
}

async function applySuggestions(){
  const list = document.getElementById('suggestions-list')
  const items = Array.from(list.querySelectorAll('.suggestion-item'))
  const titles = []
  for (let i=0;i<items.length-1;i++){
    const input = items[i].querySelector('input')
    if (input && input.value.trim()) titles.push(input.value.trim())
  }
  if (!titles.length){ alert('No titles to apply'); return }
  const r2 = await fetch(API + '/projects/' + _currentSuggestProject + '/apply_outline', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+token}, body: JSON.stringify({titles})})
  const res2 = await r2.json()
  if (r2.ok){
    closeSuggestionsPanel()
    alert('Outline applied')
    openProject(_currentSuggestProject)
  } else {
    alert(JSON.stringify(res2))
  }
}
