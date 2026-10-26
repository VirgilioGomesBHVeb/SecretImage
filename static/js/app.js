document.addEventListener('DOMContentLoaded',()=>{
  const setupDrop=(inputId,zoneId,previewId,wrapId)=>{
    const input=document.getElementById(inputId), zone=document.getElementById(zoneId), preview=document.getElementById(previewId), wrap=document.getElementById(wrapId);
    if(!input||!zone)return;
    const show=file=>{if(!file||!file.type.startsWith('image/'))return; const reader=new FileReader(); reader.onload=e=>{preview.src=e.target.result;wrap.style.display='block'}; reader.readAsDataURL(file)};
    input.addEventListener('change',()=>show(input.files[0]));
    ['dragenter','dragover'].forEach(ev=>zone.addEventListener(ev,e=>{e.preventDefault();zone.classList.add('dragover')}));
    ['dragleave','drop'].forEach(ev=>zone.addEventListener(ev,e=>{e.preventDefault();zone.classList.remove('dragover')}));
    zone.addEventListener('drop',e=>{const file=e.dataTransfer.files[0];if(file){input.files=e.dataTransfer.files;show(file)}});
  };
  setupDrop('hide-image','hide-dropzone','hide-preview','hide-preview-wrap');
  setupDrop('extract-image','extract-dropzone','extract-preview','extract-preview-wrap');
  const message=document.getElementById('message'), count=document.getElementById('char-count');
  if(message&&count){const update=()=>count.textContent=`${message.value.length} / 200000`;message.addEventListener('input',update);update()}
  document.querySelectorAll('[data-toggle]').forEach(btn=>btn.addEventListener('click',()=>{const input=document.getElementById(btn.dataset.toggle);if(input)input.type=input.type==='password'?'text':'password'}));
  document.querySelectorAll('[data-copy-target]').forEach(btn=>btn.addEventListener('click',async()=>{const el=document.getElementById(btn.dataset.copyTarget);if(!el)return;try{await navigator.clipboard.writeText(el.innerText);const old=btn.innerHTML;btn.innerHTML='✓ Copiado';setTimeout(()=>btn.innerHTML=old,1500)}catch{}}));
  document.querySelectorAll('.dropzone').forEach(z=>z.addEventListener('dragover',()=>z.style.borderColor='#258fff'));
});
