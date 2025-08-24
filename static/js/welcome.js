// === Fireworks Animation ===
if (document.getElementById("fireworks")) {
  const canvas = document.getElementById('fireworks');
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  function random(min, max) { return Math.random() * (max - min) + min; }

  class Firework {
    constructor() {
      this.x = random(0, canvas.width);
      this.y = canvas.height;
      this.targetY = random(canvas.height / 2, canvas.height / 4);
      this.color = `hsl(${Math.floor(random(0, 360))}, 100%, 50%)`;
      this.particles = [];
      this.exploded = false;
    }
    update() {
      if (!this.exploded) {
        this.y -= 5;
        if (this.y <= this.targetY) {
          this.exploded = true;
          for (let i = 0; i < 30; i++) {
            this.particles.push({
              x: this.x, y: this.y,
              speedX: random(-3, 3), speedY: random(-3, 3),
              alpha: 1, color: this.color, radius: random(2, 4)
            });
          }
        }
      } else {
        this.particles.forEach(p => {
          p.x += p.speedX; p.y += p.speedY; p.speedY += 0.1; p.alpha -= 0.02;
        });
        this.particles = this.particles.filter(p => p.alpha > 0);
      }
    }
    draw() {
      if (!this.exploded) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
      } else {
        this.particles.forEach(p => {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
          ctx.fillStyle = this.color.replace("hsl", "rgba").replace(")", `,${p.alpha})`);
          ctx.fill();
        });
      }
    }
    done() { return this.exploded && this.particles.length === 0; }
  }

  const fireworks = [];
  let startTime = Date.now();

  function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (fireworks.length < 15) { fireworks.push(new Firework()); fireworks.push(new Firework()); }
    fireworks.forEach(fw => { fw.update(); fw.draw(); });
    for (let i = fireworks.length - 1; i >= 0; i--) if (fireworks[i].done()) fireworks.splice(i, 1);

    if (Date.now() - startTime < 3000) requestAnimationFrame(loop);
    else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const msg = document.getElementById('donate-success-message');
      if (msg) msg.style.display = 'none';
      const url = new URL(window.location);
      url.searchParams.delete('donation');
      url.searchParams.delete('welcome');
      window.history.replaceState({}, document.title, url.pathname + url.search);
    }
  }
  loop();
  window.addEventListener('resize', () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; });
}

// === Ads Loader ===
const adsContainer = document.getElementById("ads-section");
if (adsContainer) {
  fetch('/static/ads.json')
    .then(r => r.json())
    .then(ads => {
      ads.forEach((ad, index) => {
        const card = document.createElement("div");
        card.classList.add("ad-card");
        card.innerHTML = `
        <div class="ad-card-inner">
          <div class="ad-card-front">
            <img src="${ad.image}" class="ad-image" alt="Ad Image" />
            <div class="ad-description">${ad.description}</div>
          </div>
          <div class="ad-card-back" style="background:white;color:black;padding:20px;">
            <h3>${ad.title || 'Объявление'}</h3>
            <p>${ad.text || 'Подробности отсутствуют.'}</p>
            <input type="number" id="donate-amount-${index}" placeholder="Сумма" min="1"/>
            <button onclick="makeDonation(${index})">Донат</button>
          </div>
        </div>`;
        card.addEventListener("click", e => {
          if (!e.target.closest("button") && !e.target.closest("input")) card.classList.toggle("flipped");
        });
        adsContainer.appendChild(card);
      });
    })
    .catch(err => console.error('Ошибка загрузки объявлений:', err));
}

function makeDonation(index) {
  const amountInput = document.getElementById(`donate-amount-${index}`);
  if (!amountInput || amountInput.value <= 0) { alert("Введите корректную сумму"); return; }
  window.location.href = `/auth/payment?amount=${encodeURIComponent(amountInput.value)}`;
}

// === Auth check ===
async function checkAuth() {
  try {
    const r = await fetch('/api/check-auth', { method: 'GET', credentials: 'include' });
    if (!r.ok) {
      const data = await r.json();
      if (data.detail === "Не авторизован") window.location.href = "/";
    }
  } catch (err) { console.error('Ошибка проверки авторизации', err); }
}
setInterval(checkAuth, 5000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) checkAuth(); });

// === Auto resize textarea ===
function autoResizeTextarea(el) {
  el.style.height = "auto";
  el.style.height = el.scrollHeight + "px";
}
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("textarea").forEach(autoResizeTextarea);
  document.addEventListener("input", e => { if (e.target.tagName.toLowerCase() === "textarea") autoResizeTextarea(e.target); });
});

// === Modal ===
const infoBtn = document.getElementById('infoBtn');
const infoModal = document.getElementById('infoModal');
const closeInfo = document.getElementById('closeInfo');
if (infoBtn && infoModal && closeInfo) {
  infoBtn.onclick = () => { infoModal.style.display = 'flex'; }
  closeInfo.onclick = () => { infoModal.style.display = 'none'; }
  window.onclick = e => { if (e.target == infoModal) infoModal.style.display = 'none'; }
}
