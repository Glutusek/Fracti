<template>
  <div class="ocr-container">
    <div class="content-wrapper">
      <div class="header">
        <button @click="goBack" class="back-btn">
          ← Powrót
        </button>
        <h1>Skanuj Paragon</h1>
      </div>

      <!-- Wybór Settlement -->
      <div class="settlement-selector" v-if="settlements.length > 0">
        <label>Przypisz do grupy rozliczeniowej:</label>
        <select v-model="selectedSettlement">
          <option :value="null">Bez grupy (tylko mój paragon)</option>
          <option v-for="settlement in settlements" :key="settlement.id" :value="settlement.id">
            {{ settlement.name }}
          </option>
        </select>
      </div>

      <!-- Upload Area -->
      <div
        class="upload-area"
        :class="{ 'drag-over': isDragging, 'has-image': previewUrl }"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          :capture="isMobile ? 'environment' : undefined"
          @change="handleFileSelect"
          style="display: none"
        />

        <div v-if="!previewUrl" class="upload-prompt">
          <div class="icon">📸</div>
          <h3>{{ isMobile ? 'Zrób zdjęcie lub wybierz z galerii' : 'Przeciągnij zdjęcie lub kliknij aby wybrać' }}</h3>
          <p class="hint">Obsługiwane formaty: JPG, PNG, HEIC</p>
        </div>

        <div v-else class="preview-container">
          <img :src="previewUrl" alt="Preview" class="preview-image" />
          <button @click.stop="clearImage" class="remove-btn">✕</button>
        </div>
      </div>

      <!-- Manual Data Entry -->
      <div class="manual-entry" v-if="previewUrl">
        <h3>Dane paragonu</h3>
        <div class="form-group">
          <label>Nazwa sklepu</label>
          <input v-model="receiptData.merchant_name" type="text" placeholder="np. Biedronka" />
        </div>

        <div class="form-group">
          <label>Data zakupu</label>
          <input v-model="receiptData.purchase_date" type="date" />
        </div>

        <div class="form-group">
          <label>Kategoria</label>
          <select v-model="receiptData.category">
            <option v-for="cat in categories" :key="cat.value" :value="cat.value">
              {{ cat.label }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Całkowita kwota (zł)</label>
          <input v-model="receiptData.total_amount" type="number" step="0.01" placeholder="0.00" />
        </div>

        <!-- Location (optional) -->
        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="includeLocation" type="checkbox" />
            Dodaj lokalizację
          </label>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="actions" v-if="previewUrl">
        <button @click="clearImage" class="btn-secondary">Anuluj</button>
        <button @click="uploadReceipt" class="btn-primary" :disabled="isUploading || !isFormValid">
          <span v-if="!isUploading">📤 Prześlij paragon</span>
          <span v-else class="spinner-inline">⏳ Przesyłanie...</span>
        </button>
      </div>

      <!-- Success/Error Messages -->
      <div v-if="successMessage" class="message success">✓ {{ successMessage }}</div>
      <div v-if="errorMessage" class="message error">✕ {{ errorMessage }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import fractiService, { type Settlement, Category } from '@/services/receipts.service';

const router = useRouter();

// State
const fileInput = ref<HTMLInputElement | null>(null);
const previewUrl = ref<string | null>(null);
const selectedFile = ref<File | null>(null);
const isDragging = ref(false);
const isUploading = ref(false);
const includeLocation = ref(false);
const selectedSettlement = ref<string | null>(null);
const settlements = ref<Settlement[]>([]);

const successMessage = ref('');
const errorMessage = ref('');

const receiptData = ref({
  merchant_name: '',
  purchase_date: new Date().toISOString().split('T')[0],
  category: Category.FOOD,
  total_amount: ''
});

// Detect mobile
const isMobile = computed(() => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
});

// Categories
const categories = fractiService.getCategoriesOptionList();

// Form validation
const isFormValid = computed(() => {
  return receiptData.value.merchant_name.trim() !== '' &&
         receiptData.value.total_amount !== '' &&
         parseFloat(receiptData.value.total_amount) > 0;
});

// Methods
const goBack = () => {
  router.push('/settlements');
};

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    processFile(target.files[0]);
  }
};

const handleDrop = (event: DragEvent) => {
  isDragging.value = false;
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    processFile(event.dataTransfer.files[0]);
  }
};

const processFile = (file: File) => {
  // Validate file type
  if (!file.type.startsWith('image/')) {
    errorMessage.value = 'Proszę wybrać plik graficzny';
    return;
  }

  selectedFile.value = file;

  // Create preview
  const reader = new FileReader();
  reader.onload = (e) => {
    previewUrl.value = e.target?.result as string;
  };
  reader.readAsDataURL(file);

  // Clear messages
  errorMessage.value = '';
  successMessage.value = '';
};

const clearImage = () => {
  previewUrl.value = null;
  selectedFile.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

const getCurrentLocation = (): Promise<{ latitude: number; longitude: number }> => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolokalizacja nie jest obsługiwana'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        });
      },
      (error) => {
        reject(error);
      }
    );
  });
};

const uploadReceipt = async () => {
  if (!selectedFile.value || !isFormValid.value) return;

  isUploading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const formData = new FormData();
    formData.append('image', selectedFile.value);
    formData.append('merchant_name', receiptData.value.merchant_name);
    formData.append('purchase_date', receiptData.value.purchase_date);
    formData.append('category', receiptData.value.category);
    formData.append('total_amount', receiptData.value.total_amount);

    if (selectedSettlement.value) {
      formData.append('settlement', selectedSettlement.value);
    }

    // Add location if requested
    if (includeLocation.value) {
      try {
        const location = await getCurrentLocation();
        formData.append('latitude', location.latitude.toString());
        formData.append('longitude', location.longitude.toString());
      } catch (locError) {
        console.warn('Nie udało się pobrać lokalizacji:', locError);
      }
    }

    await fractiService.createReceipt(formData);

    successMessage.value = 'Paragon został przesłany pomyślnie!';

    // Reset form after 2 seconds and redirect
    setTimeout(() => {
      router.push('/settlements');
    }, 2000);

  } catch (error: any) {
    console.error('Błąd przesyłania:', error);
    errorMessage.value = error.response?.data?.detail || 'Nie udało się przesłać paragonu. Spróbuj ponownie.';
  } finally {
    isUploading.value = false;
  }
};

const loadSettlements = async () => {
  try {
    settlements.value = await fractiService.getSettlements();
  } catch (error) {
    console.error('Błąd ładowania grup:', error);
  }
};

onMounted(() => {
  loadSettlements();
});
</script>

<style scoped>
.ocr-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
  padding: 2rem;
  color: #e5e7eb;
}

.content-wrapper {
  max-width: 700px;
  margin: 0 auto;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-btn {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #a78bfa;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
}

.header h1 {
  background: linear-gradient(135deg, #ffffff 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
}

/* Settlement Selector */
.settlement-selector {
  margin-bottom: 2rem;
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
}

.settlement-selector label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #a78bfa;
}

.settlement-selector select {
  width: 100%;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #e5e7eb;
  font-size: 1rem;
}

/* Upload Area */
.upload-area {
  background: rgba(139, 92, 246, 0.05);
  border: 2px dashed rgba(139, 92, 246, 0.3);
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
  position: relative;
}

.upload-area:hover {
  border-color: rgba(139, 92, 246, 0.5);
  background: rgba(139, 92, 246, 0.08);
}

.upload-area.drag-over {
  border-color: #8b5cf6;
  background: rgba(139, 92, 246, 0.15);
  transform: scale(1.02);
}

.upload-area.has-image {
  padding: 0;
  border-style: solid;
}

.upload-prompt .icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.upload-prompt h3 {
  color: #f3f4f6;
  margin-bottom: 0.5rem;
}

.upload-prompt .hint {
  color: #9ca3af;
  font-size: 0.9rem;
}

/* Preview */
.preview-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.preview-image {
  width: 100%;
  height: auto;
  max-height: 500px;
  object-fit: contain;
  border-radius: 16px;
}

.remove-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 40px;
  height: 40px;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #dc2626;
  transform: scale(1.1);
}

/* Manual Entry */
.manual-entry {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.manual-entry h3 {
  color: #a78bfa;
  margin-bottom: 1.5rem;
  font-size: 1.2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #9ca3af;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #e5e7eb;
  font-size: 1rem;
  transition: all 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #8b5cf6;
  background: rgba(0, 0, 0, 0.3);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

/* Actions */
.actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn-secondary,
.btn-primary {
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
  font-size: 1rem;
}

.btn-secondary {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #e5e7eb;
}

.btn-secondary:hover {
  background: rgba(139, 92, 246, 0.2);
}

.btn-primary {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: white;
  box-shadow: 0 5px 20px rgba(139, 92, 246, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.5);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner-inline {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

/* Messages */
.message {
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  text-align: center;
  font-weight: 500;
}

.message.success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.message.error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .ocr-container {
    padding: 1rem;
  }

  .upload-area {
    padding: 2rem 1rem;
    min-height: 250px;
  }

  .actions {
    flex-direction: column;
  }

  .btn-secondary,
  .btn-primary {
    width: 100%;
  }
}
</style>
