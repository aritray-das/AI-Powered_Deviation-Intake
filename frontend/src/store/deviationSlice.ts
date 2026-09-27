import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../api/client';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  type?: 'text' | 'extracted_text_preview';
  rawText?: string; 
}

export interface DeviationForm {
  title: string;
  site_plant: string;
  date_of_occurrence: string;
  source: string;
  related_product_material: string;
  batch_lot_number: string;
  detailed_description: string;
  initial_severity: string;
  initial_impact: string;
  severity_reason: string;
  suggested_next_action: string;
  ai_confidence: number | null;
}

interface DeviationState {
  form: DeviationForm;
  chatHistory: ChatMessage[];
  ui: {
    statusBadge: 'Draft' | 'Ready for Review' | 'Logged';
    isProcessing: boolean;
    isExtracting: boolean;
    isEditing: boolean;
    isSaving: boolean;
    fieldsRecentlyChanged: string[];
    error: string | null;
  };
  rawInput: {
    raw_input_text: string;
    input_source: 'pasted_text' | 'pdf' | null;
    original_filename: string | null;
  };
}

const initialFormState: DeviationForm = {
  title: '',
  site_plant: '',
  date_of_occurrence: '',
  source: '',
  related_product_material: '',
  batch_lot_number: '',
  detailed_description: '',
  initial_severity: '',
  initial_impact: '',
  severity_reason: '',
  suggested_next_action: '',
  ai_confidence: null,
};

const initialState: DeviationState = {
  form: initialFormState,
  chatHistory: [
    {
      id: 'greeting',
      role: 'assistant',
      content: "Paste a deviation report or email below, or upload a PDF, and I'll extract the details and run an initial risk assessment.",
      timestamp: new Date().toISOString()
    }
  ],
  ui: {
    statusBadge: 'Draft',
    isProcessing: false,
    isExtracting: false,
    isEditing: false,
    isSaving: false,
    fieldsRecentlyChanged: [],
    error: null,
  },
  rawInput: {
    raw_input_text: '',
    input_source: null,
    original_filename: null,
  },
};

export const processText = createAsyncThunk(
  'deviation/processText',
  async (text: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post('/process', { text });
      return { text, data: response.data };
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to process text');
    }
  }
);

export const extractPdf = createAsyncThunk(
  'deviation/extractPdf',
  async (file: File, { rejectWithValue }) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post('/extract/pdf', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return { filename: file.name, data: response.data };
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to extract PDF');
    }
  }
);

export const sendEditMessage = createAsyncThunk(
  'deviation/sendEditMessage',
  async (message: string, { getState, rejectWithValue }) => {
    try {
      const state = getState() as any;
      const current_state = state.deviation.form;
      const response = await apiClient.post('/deviations/edit', { message, current_state });
      return { message, data: response.data };
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to edit fields');
    }
  }
);

export const saveDeviation = createAsyncThunk(
  'deviation/saveDeviation',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as any;
      const payload = {
        ...state.deviation.form,
        raw_input_text: state.deviation.rawInput.raw_input_text,
        input_source: state.deviation.rawInput.input_source,
        original_filename: state.deviation.rawInput.original_filename,
        status: 'Logged',
      };
      const response = await apiClient.post('/deviations', payload);
      return response.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to save deviation');
    }
  }
);

const deviationSlice = createSlice({
  name: 'deviation',
  initialState,
  reducers: {
    updateFormField: (state, action: PayloadAction<{ field: keyof DeviationForm; value: any }>) => {
      (state.form as any)[action.payload.field] = action.payload.value;
    },
    clearError: (state) => {
      state.ui.error = null;
    },
    clearFieldsRecentlyChanged: (state) => {
      state.ui.fieldsRecentlyChanged = [];
    }
  },
  extraReducers: (builder) => {
    // Process Text
    builder.addCase(processText.pending, (state) => {
      state.ui.isProcessing = true;
      state.ui.error = null;
    });
    builder.addCase(processText.fulfilled, (state, action) => {
      state.ui.isProcessing = false;
      state.ui.statusBadge = 'Ready for Review';
      
      const { text, data } = action.payload;
      
      // Preserve original_filename if the source was a PDF
      if (state.rawInput.input_source !== 'pdf') {
         state.rawInput.input_source = 'pasted_text';
         state.rawInput.original_filename = null;
      }
      state.rawInput.raw_input_text = text;
      
      const updatedFields = { ...(data.extracted || {}), ...(data.assessment || {}) };
      state.form = { ...state.form, ...updatedFields };
      
      // Client-side templated summary, safely checking missing fields
      const material = state.form.related_product_material || 'material';
      const batch = state.form.batch_lot_number || 'unknown batch';
      const summaryMsg = `I've extracted the deviation details and completed an initial risk assessment for ${material} (Batch: ${batch}). Please review the form on the left.`;
      
      state.chatHistory.push({
        id: new Date().toISOString(),
        role: 'assistant',
        content: summaryMsg,
        timestamp: new Date().toISOString()
      });
    });
    builder.addCase(processText.rejected, (state, action) => {
      state.ui.isProcessing = false;
      state.ui.error = action.payload as string;
    });

    // Extract PDF
    builder.addCase(extractPdf.pending, (state) => {
      state.ui.isExtracting = true;
      state.ui.error = null;
    });
    builder.addCase(extractPdf.fulfilled, (state, action) => {
      state.ui.isExtracting = false;
      state.rawInput.original_filename = action.payload.filename;
      state.rawInput.input_source = 'pdf';
      state.rawInput.raw_input_text = action.payload.data.extracted_text;

      state.chatHistory.push({
        id: new Date().toISOString(),
        role: 'assistant',
        content: `Extracted text from ${action.payload.filename}`,
        rawText: action.payload.data.extracted_text,
        type: 'extracted_text_preview',
        timestamp: new Date().toISOString()
      });
    });
    builder.addCase(extractPdf.rejected, (state, action) => {
      state.ui.isExtracting = false;
      state.ui.error = action.payload as string;
    });

    // Send Edit Message
    builder.addCase(sendEditMessage.pending, (state, action) => {
      state.ui.isEditing = true;
      state.ui.error = null;
      state.chatHistory.push({
        id: action.meta.requestId,
        role: 'user',
        content: action.meta.arg,
        timestamp: new Date().toISOString()
      });
    });
    builder.addCase(sendEditMessage.fulfilled, (state, action) => {
      state.ui.isEditing = false;
      const { updated_state, reply, fields_changed } = action.payload.data;
      
      state.form = { ...state.form, ...updated_state };
      state.ui.fieldsRecentlyChanged = fields_changed || [];
      
      state.chatHistory.push({
        id: new Date().toISOString(),
        role: 'assistant',
        content: reply,
        timestamp: new Date().toISOString()
      });
    });
    builder.addCase(sendEditMessage.rejected, (state, action) => {
      state.ui.isEditing = false;
      state.ui.error = action.payload as string;
    });

    // Save Deviation
    builder.addCase(saveDeviation.pending, (state) => {
      state.ui.isSaving = true;
      state.ui.error = null;
    });
    builder.addCase(saveDeviation.fulfilled, (state) => {
      state.ui.isSaving = false;
      state.ui.statusBadge = 'Logged';
    });
    builder.addCase(saveDeviation.rejected, (state, action) => {
      state.ui.isSaving = false;
      state.ui.error = action.payload as string;
    });
  }
});

export const { updateFormField, clearError, clearFieldsRecentlyChanged } = deviationSlice.actions;
export default deviationSlice.reducer;
