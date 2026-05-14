
export interface Module {
  id: string;
  name: string;
  description: string;
  dependencies: string[]; // IDs or names of other modules this depends on
  constraints: string;   // Validation and constraint rules
}

export interface SchemaField {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'relation';
  required: boolean;
}

export interface DataEntity {
  id: string;
  name: string;
  fields: SchemaField[];
}

export interface TechSpec {
  basic: {
    name: string;
    type: string;
    description: string;
    targetAudience: string;
  };
  design: {
    styles: string[];
    themes: string[];
    primaryColor: string;
    mobileLayouts: string[];
    desktopLayouts: string[];
  };
  features: Module[];
  techStack: {
    frontend: string;
    ui: string;
    api: string;
    database: string;
    infrastructure: string;
    aiProvider: string;
  };
  dataSchema: DataEntity[];
}

export type Step = 1 | 2 | 3 | 4 | 5 | 6;
