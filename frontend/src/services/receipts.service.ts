import apiClient from './api';

// ==========================================
// 1. TYPY I INTERFEJSY
// ==========================================

export interface User {
  id: number;
  username: string;
}

export const Category = {
  FOOD: 'FOOD',
  TRANSPORT: 'TRANSPORT',
  ACCOMMODATION: 'ACCOMMODATION',
  ENTERTAINMENT: 'ENTERTAINMENT',
  SHOPPING: 'SHOPPING',
  SERVICES: 'SERVICES',
  OTHER: 'OTHER',
} as const;

export type CategoryType = typeof Category[keyof typeof Category];

export const CATEGORY_LABELS: Record<CategoryType, string> = {
  [Category.FOOD]: 'Jedzenie',
  [Category.TRANSPORT]: 'Transport',
  [Category.ACCOMMODATION]: 'Nocleg',
  [Category.ENTERTAINMENT]: 'Rozrywka',
  [Category.SHOPPING]: 'Zakupy',
  [Category.SERVICES]: 'Usługi',
  [Category.OTHER]: 'Inne',
};

export interface Product {
  id: number;
  name: string;
  price: string;
  category: CategoryType;
  consumers: number[];
  settlement?: string | null;
  receipt?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  created_at: string;
}

export interface Receipt {
  id: number;
  merchant_name: string;
  total_amount: string;
  purchase_date: string;
  image?: string | null;
  category: CategoryType;
  products: Product[];
  purchaser: number;
  latitude?: number | null;
  longitude?: number | null;
  created_at: string;
}

export interface Settlement {
  id: string;
  name: string;
  description: string;
  join_code: string;
  total_expenses: string;
  members: User[];
  receipts: Receipt[];
  loose_products: Product[];
  created_at: string;
  updated_at?: string;
}

// ==========================================
// 2. SERWIS API (Zwraca czyste dane)
// ==========================================

class FractiApiService {

  // --- ROZLICZENIA ---

  async getSettlements(): Promise<Settlement[]> {
    const response = await apiClient.get<Settlement[]>('/settlements/');
    return response.data; // Odpakowujemy dane tutaj
  }

  async getSettlementDetails(id: string): Promise<Settlement> {
    const response = await apiClient.get<Settlement>(`/settlements/${id}/`);
    return response.data;
  }

  async createSettlement(data: { name: string; description?: string }): Promise<Settlement> {
    const response = await apiClient.post<Settlement>('/settlements/', data);
    return response.data;
  }

  async updateSettlement(id: string, data: Partial<Settlement>): Promise<Settlement> {
    const response = await apiClient.patch<Settlement>(`/settlements/${id}/`, data);
    return response.data;
  }

  async deleteSettlement(id: string): Promise<void> {
    await apiClient.delete(`/settlements/${id}/`);
  }

  async joinSettlement(code: string): Promise<Settlement> {
    const response = await apiClient.post<Settlement>('/settlements/join/', { join_code: code });
    return response.data;
  }

  // --- PARAGONY ---

  async createReceipt(data: FormData | any): Promise<Receipt> {
    const response = await apiClient.post<Receipt>('/receipts/', data, {
      headers: {
        'Content-Type': 'multipart/form-data' // Ważne dla przesyłania plików
      }
    });
    return response.data;
  }

  // --- PRODUKTY ---

  async addLooseProduct(data: Partial<Product>): Promise<Product> {
    const response = await apiClient.post<Product>('/products/', data);
    return response.data;
  }

  // --- POMOCNICZE ---

  getCategoriesOptionList() {
    return Object.values(Category).map((cat) => ({
      value: cat,
      label: CATEGORY_LABELS[cat],
    }));
  }
}

export default new FractiApiService();