<template>
  <div class="page-wrapper">
    <div class="container">
      <div class="header-section">
        <h1 class="page-title">
          Dokumenty <span class="gradient-text">Prawne</span>
        </h1>
        <p class="page-subtitle">
          Regulamin korzystania z serwisu i polityka prywatności
        </p>
      </div>

      <div class="tabs-section">
        <div class="tabs-buttons">
          <button
            :class="['tab-button', { active: activeTab === 'terms' }]"
            @click="activeTab = 'terms'"
          >
            Regulamin
          </button>
          <button
            :class="['tab-button', { active: activeTab === 'privacy' }]"
            @click="activeTab = 'privacy'"
          >
            Polityka Prywatności
          </button>
        </div>

        <div v-if="activeTab === 'terms'" class="tab-content">
          <h2>Regulamin Korzystania z Serwisu Fracti</h2>

          <h3>1. Postanowienia Ogólne</h3>
          <p>
            Fracti to aplikacja do inteligentnego rozliczania wydatków grupowych. Niniejszy regulamin określa warunki
            korzystania z serwisu.
          </p>

          <h3>2. Warunki Korzystania</h3>
          <p>
            Korzystając z Fracti, użytkownik zobowiązuje się do:
          </p>
          <ul>
            <li>Podania rzetelnych danych podczas rejestracji</li>
            <li>Powstrzymywania się od działań zabronionych i niezgodnych z prawem</li>
            <li>Odpowiedzialności za swoją aktywność na koncie</li>
            <li>Poszanowania praw innych użytkowników</li>
          </ul>

          <h3>3. Ograniczenia Odpowiedzialności</h3>
          <p>
            Fracti udostępniana jest "tak jak jest" bez żadnych gwarancji. Twórcy aplikacji nie ponoszą
            odpowiedzialności za:
          </p>
          <ul>
            <li>Straty wynikające z błędów obliczeniowych</li>
            <li>Problemy z dostępnością usługi</li>
            <li>Utratę danych użytkownika</li>
            <li>Błędy w funkcjonalności OCR</li>
          </ul>

          <h3>4. Zmiany Regulaminu</h3>
          <p>
            Zastrzegamy sobie prawo do zmiany warunków tego regulaminu w każdym czasie. Zmiany będą skuteczne
            od momentu opublikowania nowej wersji.
          </p>

          <h3>5. Kontakt</h3>
          <p>
            W przypadku pytań dotyczących regulaminu, prosimy o kontakt na adres:
            <strong>kontakt@fracti.app</strong>
          </p>
        </div>

        <div v-if="activeTab === 'privacy'" class="tab-content">
          <h2>Polityka Prywatności</h2>

          <h3>1. Administrator Danych</h3>
          <p>
            Administrator danych osobowych: <strong>ADMIN</strong>
            <br>
            Adres: <strong>ul. Administratorska 123/45, Adminowo</strong>
            <br>
            Email: <strong>kontakt@fracti.app</strong>
          </p>

          <h3>2. Zbierane Dane Osobowe</h3>
          <p>
            W ramach korzystania z Fracti zbieramy następujące dane osobowe:
          </p>
          <ul>
            <li>Imię i nazwisko</li>
            <li>Adres e-mail</li>
            <li>Nazwa użytkownika</li>
            <li>Informacje o transakcjach i rozliczeniach</li>
            <li>Zdjęcia paragonów przesłane do funkcji OCR</li>
            <li>Dane techniczne (adres IP, rodzaj przeglądarki)</li>
          </ul>

          <h3>3. Cel Przetwarzania Danych</h3>
          <p>
            Dane osobowe przetwarzamy w celu:
          </p>
          <ul>
            <li>Świadczenia usług aplikacji</li>
            <li>Obsługi kont użytkowników</li>
            <li>Realizacji funkcji OCR do rozpoznawania paragonów</li>
            <li>Komunikacji z użytkownikami</li>
            <li>Wysyłania powiadomień i informacji o serwisie</li>
            <li>Poprawy jakości usługi</li>
            <li>Zapewnienia bezpieczeństwa usługi</li>
          </ul>

          <h3>4. Podstawa Prawna Przetwarzania</h3>
          <p>
            Przetwarzanie danych odbywa się na podstawie:
          </p>
          <ul>
            <li>Umowy zawartej z użytkownikiem (art. 6 ust. 1 lit. b RODO)</li>
            <li>Zgody użytkownika (art. 6 ust. 1 lit. a RODO)</li>
            <li>Prawnie uzasadnionych interesów (art. 6 ust. 1 lit. f RODO)</li>
          </ul>

          <h3>5. Udostępnianie Danych</h3>
          <p>
            Dane osobowe mogą być udostępniane:
          </p>
          <ul>
            <li>Innym użytkownikom w ramach wspólnych rozliczeń (nazwa, email)</li>
            <li>Dostawcom usług technicznych wspomagającym działanie aplikacji</li>
            <li>Organom władzy publicznej na podstawie obowiązującego prawa</li>
          </ul>

          <h3>6. Przechowywanie Danych</h3>
          <p>
            Dane będą przechowywane przez czas niezbędny do realizacji celów, dla których zostały zebrane,
            jednak nie dłużej niż [LICZBA LAT] lat, chyba że prawo wymaga dłuższego przechowywania.
          </p>

          <h3>7. Prawa Użytkownika</h3>
          <p>
            Każdy użytkownik ma prawo do:
          </p>
          <ul>
            <li>Dostępu do swoich danych osobowych</li>
            <li>Sprostowania danych</li>
            <li>Usunięcia danych ("prawo do bycia zapomnianym")</li>
            <li>Ograniczenia przetwarzania</li>
            <li>Przenoszenia danych</li>
            <li>Sprzeciwu wobec przetwarzania</li>
          </ul>

          <h3>8. Bezpieczeństwo Danych</h3>
          <p>
            Podejmujemy odpowiednie środki techniczne i organizacyjne, aby chronić dane przed nieuprawnionym
            dostępem, zmianą, ujawnieniem lub zniszczeniem.
          </p>

          <h3>9. Pliki Cookies</h3>
          <p>
            Serwis Fracti może wykorzystywać cookies do:
          </p>
          <ul>
            <li>Zapamiętywania preferencji użytkownika</li>
            <li>Utrzymania sesji logowania</li>
            <li>Analityki korzystania z serwisu</li>
          </ul>

          <h3>10. Kontakt w Sprawie Danych Osobowych</h3>
          <p>
            W sprawach dotyczących danych osobowych prosimy o kontakt:
            <br>
            Email: <strong>kontakt@fracti.app</strong>
            <br>
            Masz również prawo do złożenia skargi do Prezesa Urzędu Ochrony Danych Osobowych.
          </p>
        </div>
      </div>
    </div>

    <div class="bg-elements">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const activeTab = ref<'terms' | 'privacy'>('terms');
</script>

<style scoped>
.page-wrapper {
  min-height: 100vh;
  padding: 4rem 0;
  position: relative;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
  color: #e5e7eb;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1.5rem;
  position: relative;
  z-index: 1;
}

.header-section {
  text-align: center;
  margin-bottom: 3rem;
}

.page-title {
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #e5e7eb 0%, #9ca3af 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.gradient-text {
  background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 1.1rem;
  color: #9ca3af;
  max-width: 600px;
  margin: 0 auto;
}

.tabs-section {
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 1rem;
  padding: 2rem;
  backdrop-filter: blur(10px);
}

.tabs-buttons {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.tab-button {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  border-bottom: 2px solid transparent;
  position: relative;
  bottom: -1px;
}

.tab-button:hover {
  color: #8b5cf6;
}

.tab-button.active {
  color: #8b5cf6;
  border-bottom-color: #8b5cf6;
}

.tab-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.tab-content h2 {
  font-size: 1.75rem;
  margin-bottom: 1.5rem;
  color: #e5e7eb;
  border-bottom: 2px solid rgba(139, 92, 246, 0.3);
  padding-bottom: 1rem;
}

.tab-content h3 {
  font-size: 1.25rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: #8b5cf6;
}

.tab-content p {
  margin-bottom: 1rem;
  line-height: 1.6;
  color: #d1d5db;
}

.tab-content ul {
  margin-left: 1.5rem;
  margin-bottom: 1rem;
  list-style-type: disc;
}

.tab-content li {
  margin-bottom: 0.5rem;
  color: #d1d5db;
}

.tab-content strong {
  color: #8b5cf6;
}

/* Background Elements */
.bg-elements {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
  top: -100px;
  right: -100px;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  bottom: -100px;
  left: -100px;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 1.75rem;
  }

  .tabs-buttons {
    flex-direction: column;
  }

  .tab-button {
    border-bottom: none;
    border-left: 2px solid transparent;
    padding: 0.5rem 1rem;
  }

  .tab-button.active {
    border-left-color: #8b5cf6;
    border-bottom: none;
  }

  .tabs-section {
    padding: 1.5rem;
  }
}
</style>
