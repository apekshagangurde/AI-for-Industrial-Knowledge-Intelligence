// Mirror of backend/common/plant_alpha.py EQUIPMENT — keep in sync.
// Used to populate equipment pickers in the RCA and Graph tabs.
export interface Equipment {
  tag: string
  name: string
}

export const EQUIPMENT: Equipment[] = [
  { tag: 'P-101', name: 'Feed Pump' },
  { tag: 'P-102', name: 'Backup Feed Pump' },
  { tag: 'T-201', name: 'Crude Feed Tank' },
  { tag: 'V-301', name: 'Feed Line Relief Valve' },
  { tag: 'HX-401', name: 'Feed Preheater' },
  { tag: 'C-501', name: 'Instrument Air Compressor' },
]
