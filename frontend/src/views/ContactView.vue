<template>
  <div class="page-wrapper">
    <div class="container">
      <div class="header-section">
        <h1 class="page-title">
          Skontaktuj się <span class="gradient-text">z nami</span>
        </h1>
        <p class="page-subtitle">
          Masz pytania, sugestie lub napotkałeś błąd? Jesteśmy tutaj, aby pomóc.
        </p>
      </div>

      <div class="contact-grid">
        <div class="contact-card form-card">
          <h3>Napisz wiadomość</h3>
          <form @submit.prevent="sendMessage" class="contact-form">
            <div class="form-group">
              <label for="name">Imię</label>
              <input type="text" id="name" v-model="form.name" placeholder="Twoje imię" required/>
            </div>

            <div class="form-group">
              <label for="email">Email</label>
              <input type="email" id="email" v-model="form.email" placeholder="twoj@email.com" required/>
            </div>

            <div class="form-group">
              <label for="subject">Temat</label>
              <input type="text" id="subject" v-model="form.subject" placeholder="Temat wiadomości" required />
            </div>

            <div class="form-group">
              <label for="message">Wiadomość</label>
              <textarea id="message" v-model="form.message" rows="5" placeholder="W czym możemy pomóc?"
                        required></textarea>
            </div>

            <button type="submit" class="submit-button">
              Wyślij wiadomość
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path
                    d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"/>
              </svg>
            </button>
            <p v-if="errorMessage" class="error-text" style="color:#f87171;margin-top:8px">{{ errorMessage }}</p>
          </form>
        </div>

        <div class="info-column">
          <div class="contact-card info-card">
            <div class="icon-box">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <path d="M22 6l-10 7L2 6"></path>
              </svg>
            </div>
            <div>
              <h4>Email</h4>
              <p>kontakt@fracti.app</p>
              <p class="sub-text">Odpowiadamy w ciągu 24h</p>
            </div>
          </div>

          <div class="contact-card info-card">
            <div class="icon-box">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path
                    d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path>
              </svg>
            </div>
            <div>
              <h4>Twitter / X</h4>
              <p>@FractiApp</p>
              <p class="sub-text">Śledź aktualizacje</p>
            </div>
          </div>

          <div class="contact-card info-card">
            <div class="icon-box">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path
                    d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
              </svg>
            </div>
            <div>
              <h4>GitHub</h4>
              <p>Glutusek/Fracti</p>
              <p class="sub-text">Zgłoś błąd w kodzie</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-elements">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
    </div>
    <Teleport to="body">
      <div v-if="showSuccessModal" class="modal-overlay" @click="showSuccessModal = false">
        <div class="modal-content" @click.stop>
          <div class="success-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"
                 stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </div>
          <h3>Wiadomość wysłana!</h3>
          <p>Dziękujemy za kontakt. Odezwiemy się najszybciej jak to możliwe.</p>
          <button class="modal-button" @click="showSuccessModal = false">Super!</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import contactService from '@/services/contact.service';

const form = reactive({
  name: '',
  email: '',
  subject: '',
  message: ''
});

const showSuccessModal = ref(false);
const isSending = ref(false);
const errorMessage = ref<string | null>(null);
const cooldownUntil = ref<number>(0);

const sendMessage = async () => {
  if (isSending.value) return;
  if (Date.now() < cooldownUntil.value) {
    errorMessage.value = 'Proszę chwilę poczekać przed ponowną próbą.';
    return;
  }
  isSending.value = true;
  errorMessage.value = null;
  try {
    await contactService.sendContact({
      name: form.name,
      email: form.email,
      subject: form.subject,
      message: form.message,
    });
    showSuccessModal.value = true;
    form.name = '';
    form.email = '';
      form.subject = '';
      form.message = '';
  } catch (err) {
    console.error('Contact send error', err);
    // Spróbuj wydobyć komunikat z odpowiedzi serwera (np. walidacja pól)
    const resp = (err as any)?.response;
    if (resp && resp.data) {
      const data = resp.data;
      if (typeof data === 'string') {
        errorMessage.value = data;
      } else if (data.detail) {
        errorMessage.value = data.detail;
      } else {
        const parts: string[] = [];
        for (const key of Object.keys(data)) {
          const v = (data as any)[key];
          if (Array.isArray(v)) parts.push(v.join(' '));
          else if (typeof v === 'string') parts.push(v);
          else parts.push(JSON.stringify(v));
        }
        errorMessage.value = parts.join(' ');
      }
    } else {
      errorMessage.value = 'Wystąpił błąd podczas wysyłania wiadomości. Spróbuj ponownie.';
    }
  } finally {
    isSending.value = false;
    // cooldown to prevent rapid resubmits (in ms)
    cooldownUntil.value = Date.now() + 3000;
  }
};
</script>

<style scoped>
/* Specyficzne style dla Contact */
.header-section {
  text-align: center;
  margin-bottom: 4rem;
}

.page-title {
  margin-bottom: 1rem;
}

.page-subtitle {
  max-width: 600px;
  margin: 0 auto;
}

/* Grid Layout */
.contact-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

@media (max-width: 768px) {
  .contact-grid {
    grid-template-columns: 1fr;
  }
}

/* Karty */
.contact-card {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 2rem;
  backdrop-filter: blur(10px);
}

/* Formularz */
.form-card h3 {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  color: white;
}

.form-group label {
  color: #cbd5e1;
}

.submit-button {
  width: 100%;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(139, 92, 246, 0.4);
}

/* Info Cards */
.info-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  transition: transform 0.3s;
}

.info-card:hover {
  transform: translateX(5px);
  background: rgba(139, 92, 246, 0.1);
}

.icon-box {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.info-card h4 {
  margin: 0;
  color: white;
  font-size: 1.1rem;
}

.info-card p {
  margin: 0;
  color: #9ca3af;
}

.info-card .sub-text {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 0.2rem;
}

/* Tło - specyficzne orby dla Contact */
.orb-1 {
  width: 400px;
  height: 400px;
  background: #8b5cf6;
  top: 10%;
  right: -100px;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: #6366f1;
  bottom: 10%;
  left: -50px;
}

/* Modal Success - specyficzny dla Contact */
.modal-overlay {
  z-index: 9999;
  padding: 1rem;
}

.modal-content {
  text-align: center;
  max-width: 400px;
  width: 100%;
  animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.success-icon {
  width: 70px;
  height: 70px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%); /* Zielony gradient sukcesu */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  color: white;
  box-shadow: 0 5px 15px rgba(16, 185, 129, 0.3);
}

.modal-content h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: white;
}

.modal-content p {
  color: #cbd5e1;
  margin-bottom: 2rem;
  line-height: 1.5;
}

.modal-button {
  width: 100%;
  padding: 0.8rem;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.modal-button:hover {
  transform: scale(1.02);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

@keyframes popIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>