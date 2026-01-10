<template>
  <div class="page-wrapper">
    <div class="container">

      <div class="about-hero">
        <h1 class="page-title">
          Tworzymy <span class="gradient-text">Fracti</span>,<br>
          żeby ułatwić życie
        </h1>
        <p class="page-subtitle">
          Nasza misja jest prosta: koniec z kłótniami o pieniądze. Chcemy, aby wspólne wyjazdy i mieszkanie razem były wolne od stresu finansowego.
        </p>
      </div>

      <section class="story-section">
        <div class="story-content">
          <h2>Nasza Historia</h2>
          <p>
            Wszystko zaczęło się od wspólnego wyjazdu w góry. Po tygodniu świetnej zabawy spędziliśmy ostatni wieczór nad Excelem, próbując policzyć, kto zapłacił za paliwo, a kto za zakupy w schronisku.
          </p>
          <p>
            Stwierdziliśmy, że musi być lepszy sposób. Fracti powstało z potrzeby – naszej i naszych znajomych. Dziś pomagamy tysiącom grup zarządzać wydatkami bez bólu głowy.
          </p>
        </div>
        <div class="story-visual">
          <div class="visual-card">
            <span class="emoji">🚀</span>
            <strong>Prostota</strong>
          </div>
          <div class="visual-card">
            <span class="emoji">🤝</span>
            <strong>Fair Play</strong>
          </div>
          <div class="visual-card">
            <span class="emoji">💡</span>
            <strong>Technologia</strong>
          </div>
        </div>
      </section>

      <section class="values-section">
        <h2 class="section-title">Nasze Wartości</h2>
        <div class="values-grid">
          <div class="value-card">
            <div class="value-number">01</div>
            <h3>Przejrzystość</h3>
            <p>Każdy grosz się liczy. We Fracti widzisz dokładnie, na co poszły wspólne pieniądze. Żadnych ukrytych kosztów.</p>
          </div>
          <div class="value-card">
            <div class="value-number">02</div>
            <h3>Prywatność</h3>
            <p>Twoje dane finansowe są dla nas święte. Nie sprzedajemy ich reklamodawcom. Służą tylko Tobie.</p>
          </div>
          <div class="value-card">
            <div class="value-number">03</div>
            <h3>Automatyzacja</h3>
            <p>Wierzymy, że technologia (jak OCR paragonów) powinna wykonywać nudną robotę za Ciebie.</p>
          </div>
        </div>
      </section>

    </div>
     <div class="bg-elements">
      <div class="orb orb-center"></div>
    </div>
  </div>
</template>

<style scoped>
/* Specjalne nadpisanie dla AboutUs */
.container {
  max-width: 1000px;
}

/* Story Section */
.story-section {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 4rem;
  margin-bottom: 6rem;
  align-items: center;
}

.story-content h2 {
  font-size: 2rem;
  color: white;
  margin-bottom: 1.5rem;
}

.story-content p {
  color: #cbd5e1;
  font-size: 1.1rem;
  line-height: 1.7;
  margin-bottom: 1.5rem;
}

.story-visual {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.visual-card {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  padding: 1rem 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 1.2rem;
  color: white;
  transition: transform 0.3s;
}

.visual-card:hover {
  transform: translateX(10px);
  background: rgba(139, 92, 246, 0.2);
}

.visual-card .emoji {
  font-size: 1.5rem;
}

/* Values Section */
.values-section {
  margin-bottom: 4rem;
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  margin-bottom: 3rem;
  color: white;
}

.values-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.value-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 2.5rem;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.value-card:hover {
  transform: translateY(-5px);
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.value-number {
  font-size: 4rem;
  font-weight: 900;
  color: rgba(139, 92, 246, 0.1);
  position: absolute;
  top: -10px;
  right: 10px;
  line-height: 1;
}

.value-card h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #f3f4f6;
  position: relative;
}

.value-card p {
  color: #9ca3af;
  line-height: 1.6;
  position: relative;
}

/* Background - specjalny orb dla AboutUs */
.orb-center {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
}

@media (max-width: 768px) {
  .story-section {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
}
</style>