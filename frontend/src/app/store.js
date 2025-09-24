import { configureStore } from '@reduxjs/toolkit';
import configReducer from '../features/config/configSlice.js';
import consoleReducer from '../features/console/consoleSlice.js';
import servicesReducer from '../features/services/servicesSlice.js';

export const store = configureStore({
  reducer: {
    config: configReducer,
    console: consoleReducer,
    services: servicesReducer
  }
});
