import apiClient from "./api";

// ==========================================
// 1. TYPY I INTERFEJSY
// ==========================================

export interface User {
  id: number;
  username: string;
  first_name?: string;
}

export const Category = {
  FOOD: "FOOD",
  TRANSPORT: "TRANSPORT",
  ACCOMMODATION: "ACCOMMODATION",
  ENTERTAINMENT: "ENTERTAINMENT",
  SHOPPING: "SHOPPING",
  SERVICES: "SERVICES",
  OTHER: "OTHER",
} as const;

export type CategoryType = (typeof Category)[keyof typeof Category];

export const CATEGORY_LABELS: Record<CategoryType, string> = {
  [Category.FOOD]: "Jedzenie",
  [Category.TRANSPORT]: "Transport",
  [Category.ACCOMMODATION]: "Nocleg",
  [Category.ENTERTAINMENT]: "Rozrywka",
  [Category.SHOPPING]: "Zakupy",
  [Category.SERVICES]: "Usługi",
  [Category.OTHER]: "Inne",
};

export interface Product {
  id: number;
  name: string;
  description?: string | null;
  price: string;

  category: CategoryType;
  consumers: number[];
  purchaser?: number | null;
  settlement?: string | null;
  receipt?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  created_at: string;
}

export interface Receipt {
  id: string;
  merchant_name: string;
  description?: string | null;
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
  owner_id?: number;
}

// ==========================================
// 2. SERWIS API (Zwraca czyste dane)
// ==========================================

class FractiApiService {
  // --- ROZLICZENIA ---

  async getSettlements(): Promise<Settlement[]> {
    const response = await apiClient.get<Settlement[]>("/settlements/");
    return response.data; // Odpakowujemy dane tutaj
  }

  async getSettlementDetails(id: string): Promise<Settlement> {
    const response = await apiClient.get<Settlement>(`/settlements/${id}/`);
    return response.data;
  }

  async createSettlement(data: {
    name: string;
    description?: string;
  }): Promise<Settlement> {
    const response = await apiClient.post<Settlement>("/settlements/", data);
    return response.data;
  }

  async updateSettlement(
    id: string,
    data: Partial<Settlement>,
  ): Promise<Settlement> {
    const response = await apiClient.patch<Settlement>(
      `/settlements/${id}/`,
      data,
    );
    return response.data;
  }

  async deleteSettlement(id: string): Promise<void> {
    await apiClient.delete(`/settlements/${id}/`);
  }

  async joinSettlement(code: string): Promise<Settlement> {
    const response = await apiClient.post<Settlement>("/settlements/join/", {
      join_code: code,
    });
    return response.data;
  }

  async removeMember(settlementId: string, userId: number): Promise<void> {
    await apiClient.post(`/settlements/${settlementId}/remove-member/`, {
      user_id: userId,
    });
  }

  // --- PARAGONY ---

  async createReceipt(data: FormData | any): Promise<Receipt> {
    const response = await apiClient.post<Receipt>("/receipts/", data, {
      headers: {
        "Content-Type": "multipart/form-data", // Ważne dla przesyłania plików
      },
    });
    return response.data;
  }

  // --- PRODUKTY ---

  async addLooseProduct(data: Partial<Product>): Promise<Product> {
    const response = await apiClient.post<Product>("/products/", data);
    return response.data;
  }

  async updateProduct(id: number, data: Partial<Product>): Promise<Product> {
    const response = await apiClient.patch<Product>(`/products/${id}/`, data);
    return response.data;
  }

  async deleteProduct(id: number): Promise<void> {
    await apiClient.delete(`/products/${id}/`);
  }

  // --- PARAGONY - EDYCJA ---

  async updateReceipt(id: number, data: Partial<Receipt>): Promise<Receipt> {
    const response = await apiClient.patch<Receipt>(`/receipts/${id}/`, data);
    return response.data;
  }

  async deleteReceipt(id: number): Promise<void> {
    await apiClient.delete(`/receipts/${id}/`);
  }

  // --- POZYCJE PARAGONU ---

  async addReceiptItem(
    receiptId: string,
    data: Partial<Product>,
  ): Promise<Product> {
    const response = await apiClient.post<Product>("/products/", {
      ...data,
      receipt: receiptId,
    });
    return response.data;
  }

  async updateReceiptItem(
    itemId: number,
    data: Partial<Product>,
  ): Promise<Product> {
    const response = await apiClient.patch<Product>(
      `/products/${itemId}/`,
      data,
    );
    return response.data;
  }

  async deleteReceiptItem(itemId: number): Promise<void> {
    await apiClient.delete(`/products/${itemId}/`);
  }

  // --- OCR ---

  async analyzeReceipt(
    formData: FormData,
  ): Promise<{ task_id: string; status: string }> {
    // ZMIANA: Adres URL zmieniony z '/receipts/analyze/' na '/ocr/analyze/'
    const response = await apiClient.post<{ task_id: string; status: string }>(
      "/ocr/analyze/",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return response.data;
  }

  async getOCRResult(taskId: string): Promise<any> {
    // ZMIANA: Adres URL zmieniony z '/receipts/result/...' na '/ocr/result/...'
    const response = await apiClient.get(`/ocr/result/${taskId}/`);
    return response.data;
  }
  // --- POMOCNICZE ---

  getCategoriesOptionList() {
    return Object.values(Category).map((cat) => ({
      value: cat,
      label: CATEGORY_LABELS[cat],
    }));
  }
  async addGuestUser(settlementId: string, name: string) {
    const response = await apiClient.post(
      `settlements/${settlementId}/add-guest/`,
      {
        name: name,
      },
    );
    return response.data;
  }

  async settleDebt(
    settlementId: string,
    fromUserId: number,
    toUserId: number,
    amount: number,
  ): Promise<any> {
    const response = await apiClient.post(
      `/settlements/${settlementId}/settle-debt/`,
      {
        from_user: fromUserId,
        to_user: toUserId,
        amount: amount,
      },
    );
    return response.data;
  }

  async undoSettleDebt(settlementId: string, debtId: string): Promise<any> {
    const response = await apiClient.delete(
      `/settlements/${settlementId}/settle-debt/${debtId}/`,
    );
    return response.data;
  }

  // --- HEATMAP ---

  async getHeatmapData(
    settlementId: string,
    bbox: [number, number, number, number], // [min_lon, min_lat, max_lon, max_lat]
    cellSize?: number, // Cell size in degrees (optional)
    dateFrom?: string,
    dateTo?: string,
    categories?: string[],
    userIds?: number[],
  ): Promise<any> {
    const params = new URLSearchParams();
    params.append("bbox", bbox.join(","));
    
    if (cellSize) {
      params.append("cell_size", cellSize.toString());
    }

    if (dateFrom) params.append("date_from", dateFrom);
    if (dateTo) params.append("date_to", dateTo);
    if (categories && categories.length > 0) {
      params.append("categories", categories.join(","));
    }
    if (userIds && userIds.length > 0) {
      params.append("user_ids", userIds.join(","));
    }

    const response = await apiClient.get(
      `/settlements/${settlementId}/heatmap/?${params.toString()}`,
    );
    return response.data;
  }
}

export default new FractiApiService();
