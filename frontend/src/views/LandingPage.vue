<template>
  <div class="landing-page">

    <!-- Hero Section -->
    <section class="hero">
      <div class="container">
        <h1 class="hero-title">
          Rozliczaj wydatki<br />
          <span class="gradient-text">łatwo i sprawnie</span>
        </h1>
        <p class="hero-subtitle">
          Zarządzaj kosztami wspólnymi, skanuj paragony i śledź swoje wydatki w jednym miejscu
        </p>

        <router-link v-if="!isLoggedIn" to="/auth" class="cta-button">
          Utwórz konto
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 3L9 4L15 10L9 16L10 17L17 10L10 3Z" />
          </svg>
        </router-link>

        <router-link v-else to="/settlements" class="cta-button">
          Przejdź do rozliczeń
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 3L9 4L15 10L9 16L10 17L17 10L10 3Z" />
          </svg>
        </router-link>
      </div>
      <div class="hero-background">
        <div class="gradient-orb orb-1"></div>
        <div class="gradient-orb orb-2"></div>
        <div class="gradient-orb orb-3"></div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features" id="features">
      <div class="container">
        <h2 class="section-title">Funkcje</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <path d="M16 4L28 10V18C28 24 16 28 16 28C16 28 4 24 4 18V10L16 4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 16L15 19L21 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>Rozliczenia między użytkownikami</h3>
            <p>Łatwo zarządzaj kosztami wspólnymi. Zaproś znajomych i sprawiedliwie rozlicz wydatki grupowe.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <rect x="6" y="8" width="20" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                <path d="M10 14H22M10 18H18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M16 8V6M12 6H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>OCR paragonów</h3>
            <p>Zeskanuj paragon aparatem i automatycznie wyodrębnij wszystkie pozycje dzięki zaawansowanej technologii OCR.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <circle cx="16" cy="16" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M16 8V16L20 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>Automatyczne rozliczenia</h3>
            <p>System automatycznie oblicza, kto komu ile winien i optymalizuje przepływy pieniężne w grupie.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <path d="M28 16C28 22.6274 22.6274 28 16 28C9.37258 28 4 22.6274 4 16C4 9.37258 9.37258 4 16 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M24 8L16 16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <circle cx="24" cy="8" r="4" fill="currentColor"/>
              </svg>
            </div>
            <h3>Mapa z markerami</h3>
            <p>Zaznaczaj miejsca wydatków na mapie i śledź, gdzie najczęściej robisz zakupy.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it Works Section -->
    <section class="how-it-works">
      <div class="container">
        <h2 class="section-title">Jak to działa</h2>
        <div class="steps">
          <div class="step">
            <div class="step-number">1</div>
            <h3>Utwórz konto</h3>
            <p>Zarejestruj się w kilka sekund i zacznij zarządzać wydatkami</p>
          </div>

          <div class="step">
            <div class="step-number">2</div>
            <h3>Zaproś znajomych</h3>
            <p>Dodaj osoby, z którymi dzielisz koszty</p>
          </div>
          <div class="step">
            <div class="step-number">3</div>
            <h3>Dodaj wydatki</h3>
            <p>Zeskanuj paragon lub wprowadź wydatek ręcznie</p>
          </div>
          <div class="step">
            <div class="step-number">4</div>
            <h3>Rozlicz się</h3>
            <p>Zobacz, kto komu ile winien i zakończ rozliczenie</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section v-if="!isLoggedIn" class="cta-section" id="about">
      <div class="container">
        <h2 class="section-title">Rozpocznij już dziś</h2>
        <p class="cta-description">
          Dołącz do tysięcy użytkowników, którzy zarządzają swoimi wydatkami sprawniej
        </p>
        <router-link to="/auth" class="cta-button large">
          Utwórz darmowe konto
        </router-link>
      </div>
    </section>


  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { computed } from 'vue';

const authStore = useAuthStore();
const isLoggedIn = computed(() => authStore.isLoggedIn);
const currentYear = new Date().getFullYear();
</script>

<style scoped>
.landing-page {
  flex: 1;
  background: var(--gradient-page-dark);
  color: var(--text-primary);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

/* Hero Section */
.hero {
  position: relative;
  min-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.3;
  animation: float 20s infinite ease-in-out;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  top: -200px;
  left: -100px;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #6366f1 0%, transparent 70%);
  bottom: -150px;
  right: -100px;
  animation-delay: -5s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #a855f7 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(50px, -50px) scale(1.1);
  }
  66% {
    transform: translate(-50px, 50px) scale(0.9);
  }
}

.hero .container {
  position: relative;
  z-index: 1;
  text-align: center;
}

.hero-title {
  font-size: 4rem;
  font-weight: 800;
  margin-bottom: 1.5rem;
  line-height: 1.2;
  text-shadow: 0 0 40px rgba(139, 92, 246, 0.3);
}

.gradient-text {
  background: var(--gradient-button);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: #9ca3af;
  margin-bottom: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 2.5rem;
  background: var(--gradient-button);
  color: white;
  text-decoration: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1.1rem;
  transition: all 0.3s;
  box-shadow: 0 10px 40px rgba(139, 92, 246, 0.3);
}

.cta-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 50px rgba(139, 92, 246, 0.5);
}

.cta-button.large {
  padding: 1.25rem 3rem;
  font-size: 1.25rem;
}

/* Features Section */
.features {
  padding: 6rem 0;
  position: relative;
  z-index: 1;
}

.section-title {
  text-align: center;
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 4rem;
  background: var(--gradient-card);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.features-grid {
  display: grid;
  /*grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));*/
  grid-template-columns: repeat(2, 1fr);
  gap: 2rem;
}

.feature-card {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 2rem;
  transition: all 0.3s;
}

.feature-card:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.4);
  transform: translateY(-5px);
  box-shadow: 0 10px 40px rgba(139, 92, 246, 0.2);
}

.feature-icon {
  width: 64px;
  height: 64px;
  background: var(--gradient-button);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  color: white;
}

.feature-card h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #f3f4f6;
}

.feature-card p {
  color: #9ca3af;
  line-height: 1.6;
}

/* How it Works Section */
.how-it-works {
  padding: 6rem 0;
  background: rgba(0, 0, 0, 0.2);
}

.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.step {
  flex: 1;
  min-width: 200px;
  max-width: 250px;
  text-align: center;
}

.step-number {
  width: 60px;
  height: 60px;
  background: var(--gradient-button);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 auto 1rem;
  box-shadow: 0 5px 20px rgba(139, 92, 246, 0.4);
}

.step h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: #f3f4f6;
}

.step p {
  color: #9ca3af;
  font-size: 0.95rem;
}

/* CTA Section */
.cta-section {
  padding: 6rem 0;
  text-align: center;
}

.cta-description {
  font-size: 1.25rem;
  color: #9ca3af;
  margin-bottom: 2rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}
@media (768px <= width <= 975px) {
  .steps{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    justify-items: center;
  }
  .step{
    min-width: auto;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }

  .hero-subtitle {
    font-size: 1rem;
  }

  .section-title {
    font-size: 1.5rem;
  }

  .step-arrow {
    display: none;
  }

  .steps {
    flex-direction: column;
  }
  .features-grid {
    grid-template-columns: 1fr;
  }

  .step {
    padding: 1rem;
  }

  .feature-card {
    padding: 1.5rem;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 1.5rem;
  }

  .hero-subtitle {
    font-size: 0.9rem;
  }

  .section-title {
    font-size: 1.2rem;
  }

  .step {
    padding: 0.75rem;
  }

  .step-number {
    width: 40px;
    height: 40px;
    font-size: 1.2rem;
  }

  .feature-card {
    padding: 1rem;
  }

  .feature-icon {
    font-size: 2rem;
  }

  button {
    padding: 8px 16px;
    font-size: 0.9rem;
  }
}
</style>
