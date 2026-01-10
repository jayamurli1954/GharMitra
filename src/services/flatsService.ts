/**
 * Flats Service
 * Manages flat/apartment data
 */
import api from './api';

export interface Flat {
  id: string;
  flat_number: string;
  area_sqft: number;
  bedrooms?: number; // Number of bedrooms (2 or 3)
  occupants: number;
  owner_name: string;
  owner_phone?: string;
  owner_email?: string;
  created_at: string;
  updated_at: string;
}

export interface FlatCreate {
  flat_number: string;
  area_sqft: number;
  bedrooms?: number; // Number of bedrooms (2 or 3)
  occupants: number;
  owner_name: string;
  owner_phone?: string;
  owner_email?: string;
}

export interface FlatUpdate {
  area_sqft?: number;
  bedrooms?: number; // Number of bedrooms (2 or 3)
  occupants?: number;
  owner_name?: string;
  owner_phone?: string;
  owner_email?: string;
}

export interface FlatsSummary {
  total_flats: number;
  total_area: number;
  total_occupants: number;
  avg_area: number;
  avg_occupants: number;
}

export const flatsService = {
  /**
   * Get all flats
   */
  async getFlats(): Promise<Flat[]> {
    const response = await api.get<any[]>('/flats');
    
    // Map _id to id (backend returns _id but frontend expects id)
    const mappedFlats: Flat[] = response.data.map((flat: any) => ({
      ...flat,
      id: flat.id || flat._id || String(flat._id), // Use _id if id is missing
    }));
    
    // Log the response to verify structure
    if (mappedFlats.length > 0) {
      console.log('📋 API Response - First flat:', {
        original: response.data[0],
        mapped: mappedFlats[0],
        hasId: !!mappedFlats[0].id,
        idValue: mappedFlats[0].id,
      });
    }
    
    return mappedFlats;
  },

  /**
   * Get a specific flat by ID
   */
  async getFlat(flatId: string): Promise<Flat> {
    const response = await api.get<any>(`/flats/${flatId}`);
    // Map _id to id
    return {
      ...response.data,
      id: response.data.id || response.data._id || String(response.data._id),
    };
  },

  /**
   * Create a new flat
   */
  async createFlat(data: FlatCreate): Promise<Flat> {
    const response = await api.post<any>('/flats', data);
    // Map _id to id
    return {
      ...response.data,
      id: response.data.id || response.data._id || String(response.data._id),
    };
  },

  /**
   * Update a flat
   */
  async updateFlat(flatId: string, data: FlatUpdate): Promise<Flat> {
    console.log('📝 Updating flat - Request:', {
      flatId: flatId,
      flatIdType: typeof flatId,
      url: `/flats/${flatId}`,
      data: data,
    });
    
    try {
      const response = await api.put<any>(`/flats/${flatId}`, data);
      // Map _id to id
      const mappedFlat = {
        ...response.data,
        id: response.data.id || response.data._id || String(response.data._id),
      };
      console.log('✅ Update successful:', mappedFlat);
      return mappedFlat;
    } catch (error: any) {
      console.error('❌ Update failed:', {
        flatId: flatId,
        error: error.message,
        status: error.response?.status,
        data: error.response?.data,
      });
      throw error;
    }
  },

  /**
   * Delete a flat
   */
  async deleteFlat(flatId: string): Promise<void> {
    console.log('🗑️ Deleting flat - Request:', {
      flatId: flatId,
      flatIdType: typeof flatId,
      url: `/flats/${flatId}`,
    });
    
    try {
      await api.delete(`/flats/${flatId}`);
      console.log('✅ Delete successful');
    } catch (error: any) {
      console.error('❌ Delete failed:', {
        flatId: flatId,
        error: error.message,
        status: error.response?.status,
        data: error.response?.data,
      });
      throw error;
    }
  },

  /**
   * Get flats summary statistics
   */
  async getFlatsSummary(): Promise<FlatsSummary> {
    const response = await api.get<FlatsSummary>('/flats/statistics/summary');
    return response.data;
  },
};
