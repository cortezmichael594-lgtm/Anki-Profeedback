(() => {
  'use strict';
  const DELAY = 140;

  const wrap = (btn) => {
    if (!btn || btn.__vfxWrapped) return;
    const original = btn.onclick;
    if (!original) return;
    btn.__vfxWrapped = true;
    btn.onclick = null;
    btn.addEventListener(
      'click',
      (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();
        btn.classList.add('pressed');
        window.setTimeout(() => original.call(btn, event), DELAY);
      },
      true
    );
  };

  const wrapAll = () => {
    const answer = document.getElementById('ansbut');
    if (answer) wrap(answer);
    document
      .querySelectorAll(
        "button[onclick*='ease1'],button[onclick*='ease2']," +
          "button[onclick*='ease3'],button[onclick*='ease4']"
      )
      .forEach(wrap);
    const middle = document.getElementById('middle');
    if (middle) {
      middle.style.display = 'flex';
      middle.style.justifyContent = 'center';
      middle.style.width = '100%';
    }
  };

  if (document.readyState !== 'loading') {
    wrapAll();
  } else {
    document.addEventListener('DOMContentLoaded', wrapAll, { once: true });
  }

  let debounce = null;
  const observer = new MutationObserver(() => {
    window.clearTimeout(debounce);
    debounce = window.setTimeout(wrapAll, 30);
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
