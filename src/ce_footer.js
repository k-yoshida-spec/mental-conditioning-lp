class {{CLASS}} extends HTMLElement{
  static get observedAttributes(){return ['sent'];}
  attributeChangedCallback(n,o,v){ if(n!=='sent'||!this.shadowRoot) return; this._sending=false;
    const R=this.shadowRoot,msg=R.querySelector('[data-ka-sent]'),btn=R.querySelector('form [type=submit]'); if(!msg) return;
    if(String(v).startsWith('ok')){msg.textContent=msg.dataset.ok||'送信しました。';const f=R.querySelector('form');f&&f.reset&&f.reset();}
    else if(String(v).startsWith('ng')){msg.textContent=msg.dataset.ng||'送信できませんでした。';}
    msg.hidden=false; if(btn) btn.disabled=false; }
  connectedCallback(){
    if(this._done) return; this._done=true;
    const D=window.document;
    FONTS.forEach(h=>{ if(!D.querySelector('link[href="'+h+'"]')){const l=D.createElement('link');l.rel='stylesheet';l.href=h;D.head.appendChild(l);} });
    const R=this.attachShadow({mode:'open'});
    R.innerHTML='<style>'+CSS+'</style><div class="kroot">'+HTML+'</div>';
    const root=R.querySelector('.kroot');
    const shim={
      querySelector:s=>R.querySelector(s), querySelectorAll:s=>R.querySelectorAll(s),
      getElementById:id=>R.getElementById(id), createElement:n=>D.createElement(n), createElementNS:(a,b)=>D.createElementNS(a,b),
      createTextNode:t=>D.createTextNode(t),
      addEventListener:(t,f,o)=>R.addEventListener(t,f,o),
      get activeElement(){return R.activeElement;},
      body:root, documentElement:root, head:D.head
    };
    try{ run(shim,R); }catch(e){ console.error('[{{TAG}}]',e); }
    const fit=()=>{const h=root.scrollHeight; if(h&&this._h!==h){this._h=h;this.style.height=h+'px';}};
    new ResizeObserver(fit).observe(root); fit();
  }
}
if(!customElements.get('{{TAG}}')) customElements.define('{{TAG}}',{{CLASS}});
})();
