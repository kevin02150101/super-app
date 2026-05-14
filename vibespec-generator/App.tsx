
import React, { useState, useEffect } from 'react';
import { 
  Plus, Trash2, ArrowRight, ArrowLeft, Save, 
  Settings, Layout, Layers, Database, Sparkles, FileText,
  Github, Monitor, Smartphone, Palette, CheckCircle2,
  Info, Lightbulb, Moon, Sun, ChevronDown, HelpCircle,
  Wand2, Loader2, X, Check, Box, LayoutGrid, Code2, Server, Globe
} from 'lucide-react';
import { TechSpec, Step, Module, DataEntity } from './types';
import { refineSpecWithAI, assistField } from './services/geminiService';

const INITIAL_SPEC: TechSpec = {
  basic: { name: '', type: 'RWD Responsive Web App', description: '', targetAudience: '' },
  design: { 
    styles: ['Modern SaaS (Clean Business)'], 
    themes: ['Auto (System)'], 
    primaryColor: '#3b82f6',
    mobileLayouts: ['Bottom Nav'],
    desktopLayouts: ['Sidebar']
  },
  features: [],
  techStack: {
    frontend: 'Next.js (App Router)',
    ui: 'Shadcn UI + Tailwind CSS',
    api: 'Node.js (Express)',
    database: 'PostgreSQL',
    infrastructure: 'Vercel',
    aiProvider: 'Gemini API'
  },
  dataSchema: []
};

const GLOSSARY: Record<string, string> = {
  'RWD': 'Responsive Web Design: pages automatically adapt to any screen size, from large desktops to small phones, without breaking the layout.',
  'PWA': 'Progressive Web App: lets your website be installed on a phone home screen like a native app, and even work offline.',
  'Next.js': 'A high-performance React framework — fast page loads and great SEO out of the box.',
  'UI Library': 'Like a Lego set for the web: pre-built, polished components you can snap together for a professional UI.',
  'Supabase': 'A cloud backend that handles auth, database, and file storage for you so you can focus on the product.',
  'SaaS': 'Software as a Service — professional tools you access through the browser, like Google Drive.',
  'Vibe Coding': 'A new way of building software where you describe the vibe and intent, and AI writes the code with you.',
  'Schema': 'The blueprint of your database — defines how data is organized and related.',
  'JWT': 'A digital pass that tells the server who the user is, so they don\'t have to log in on every request.',
  'Frontend': 'The part of the app the user sees and interacts with in the browser.',
  'Backend': 'The server-side brain that runs business logic, handles payments, and stores data.',
  'Database': 'A secure vault where all of your application\'s data is stored.'
};

const FIXED_DEPENDENCIES = [
  'User Authentication (Auth)',
  'Database Connection (DB)',
  'Image / File Upload',
  'Stripe Payments',
  'Email / SMS Notifications',
  'Gemini AI Integration'
];

const DESIGN_OPTIONS = {
  styles: [
    'Modern SaaS (Clean Business)', 'Glassmorphism', 'Neo-Brutalism', 
    'Minimalist', 'Cyberpunk (Dark Neon)', 'Bento Grid',
    'Claymorphism', 'Material Design', 'Flat Design 2.0'
  ],
  themes: ['Light', 'Dark', 'Auto (System)', 'High Contrast'],
  mobileLayouts: [
    'Bottom Nav', 'Side Drawer', 'Floating Action Button (FAB)', 
    'Full-screen Gestures', 'Card Stack', 'List / Detail View'
  ],
  desktopLayouts: [
    'Sidebar', 'Top Navbar', 'Dashboard Grid', 
    'Multi-column Layout', 'Masonry Grid', 'Split View'
  ]
};

// Tech stack options and mappings
const TECH_OPTIONS = {
  frontend: ['Next.js (App Router)', 'React (Vite)', 'Vue 3 (Nuxt)', 'Svelte (SvelteKit)'],
  ui: ['Shadcn UI + Tailwind CSS', 'Material UI (MUI)', 'Mantine UI', 'Headless UI', 'Daisy UI'],
  api: ['Node.js (Express)', 'Python (FastAPI)', 'Java Spring Boot', 'C# .Net Core', 'Go (Gin)'],
  database: ['PostgreSQL', 'MySQL', 'MongoDB', 'Supabase (BaaS)', 'Firebase (BaaS)', 'Redis'],
  infrastructure: ['Vercel', 'AWS', 'GCP', 'Azure', 'Netlify', 'Docker (Self-host)']
};

const UI_MAPPING: Record<string, string> = {
  'Next.js (App Router)': 'Shadcn UI + Tailwind CSS',
  'React (Vite)': 'Mantine UI',
  'Vue 3 (Nuxt)': 'Headless UI',
  'Svelte (SvelteKit)': 'Daisy UI'
};

export default function App() {
  const [step, setStep] = useState<Step>(1);
  const [spec, setSpec] = useState<TechSpec>(INITIAL_SPEC);
  const [isRefining, setIsRefining] = useState(false);
  const [refinedMarkdown, setRefinedMarkdown] = useState<string | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('vibe-theme') as 'light' | 'dark') || 'light';
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('vibe-theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  const updateSpec = <K extends keyof TechSpec>(key: K, value: TechSpec[K]) => {
    setSpec(prev => ({ ...prev, [key]: value }));
  };

  const goToStep = (s: number) => setStep(s as Step);

  const handleRefine = async () => {
    setIsRefining(true);
    const result = await refineSpecWithAI(spec);
    setRefinedMarkdown(result);
    setIsRefining(false);
    setStep(6);
  };

  const renderStep = () => {
    switch(step) {
      case 1: return <Step1Basic spec={spec} updateSpec={updateSpec} />;
      case 2: return <Step2Design spec={spec} updateSpec={updateSpec} />;
      case 3: return <Step3Features spec={spec} updateSpec={updateSpec} />;
      case 4: return <Step4Tech spec={spec} updateSpec={updateSpec} />;
      case 5: return <Step5Schema spec={spec} updateSpec={updateSpec} />;
      case 6: return <Step6Preview spec={spec} refinedMarkdown={refinedMarkdown} isRefining={isRefining} onRefine={handleRefine} />;
    }
  };

  return (
    <div className={`min-h-screen flex flex-col transition-all duration-500 ease-in-out ${theme === 'dark' ? 'bg-[#020617] text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      <header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50 px-4 py-3 sm:px-8 shadow-sm transition-colors duration-500">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer group" onClick={() => goToStep(1)}>
            <div className="w-11 h-11 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center text-white shadow-lg group-hover:rotate-6 transition-transform">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-black tracking-tight leading-none flex items-center gap-1.5 dark:text-white">
                VibeSpec <TermHelp term="Vibe Coding" />
              </h1>
              <p className="text-[10px] text-blue-600 dark:text-blue-400 font-bold uppercase tracking-[0.2em] mt-1">AI Tech Spec Generator</p>
            </div>
          </div>
          <div className="hidden lg:flex items-center gap-2">
            <StepIndicator currentStep={step} onStepClick={goToStep} />
          </div>
          <div className="flex items-center gap-2">
            <button onClick={toggleTheme} className="p-2.5 text-slate-500 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-all duration-300">
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-6 sm:py-10 flex flex-col mb-24 lg:mb-0 transition-all duration-500">
        <div className="bg-white/95 dark:bg-slate-900/90 backdrop-blur-xl rounded-[2.5rem] p-6 sm:p-12 shadow-2xl border border-white dark:border-slate-800/50 flex-1 flex flex-col min-h-[600px] animate-in fade-in duration-700 transition-colors duration-500">
          <div className="flex-1">
            {renderStep()}
          </div>
        </div>
      </main>

      <footer className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border-t border-slate-200 dark:border-slate-800 fixed bottom-0 left-0 right-0 p-4 lg:p-5 z-50 shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.1)] transition-colors duration-500">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
          <button onClick={() => setStep(s => Math.max(s - 1, 1) as Step)} disabled={step === 1} className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-bold transition-all ${step === 1 ? 'opacity-30 pointer-events-none' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'}`}>
            <ArrowLeft className="w-5 h-5" /> <span className="hidden sm:inline">Back</span>
          </button>
          <div className="flex gap-2 items-center lg:hidden">
             <span className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">STEP {step}/6</span>
          </div>
          {step < 5 ? (
            <button onClick={() => setStep(s => Math.min(s + 1, 6) as Step)} className="flex items-center gap-2 bg-slate-900 dark:bg-blue-600 text-white px-8 py-3 rounded-2xl font-bold hover:shadow-xl transition-all active:scale-95 shadow-blue-500/10">
              Next Step <ArrowRight className="w-5 h-5" />
            </button>
          ) : step === 5 ? (
            <button onClick={() => setStep(6)} className="flex items-center gap-2 bg-blue-600 text-white px-8 py-3 rounded-2xl font-bold hover:bg-blue-700 transition-all shadow-xl shadow-blue-600/30 active:scale-95">
              View Summary <FileText className="w-5 h-5" />
            </button>
          ) : (
            <button onClick={handleRefine} disabled={isRefining} className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-10 py-3 rounded-2xl font-black hover:shadow-2xl hover:-translate-y-1 transition-all disabled:opacity-50 active:scale-95 shadow-lg shadow-blue-500/30">
              {isRefining ? 'AI is refining...' : 'Refine with AI'} <Sparkles className="w-5 h-5" />
            </button>
          )}
        </div>
      </footer>
    </div>
  );
}

function TermHelp({ term }: { term: string }) {
  const explanation = GLOSSARY[term] || 'Technical term description.';
  return (
    <div className="group relative inline-flex items-center align-middle">
      <HelpCircle className="w-3.5 h-3.5 text-blue-400 dark:text-blue-500 cursor-help ml-1 group-hover:scale-125 transition-all duration-300" />
      <div className="pointer-events-none absolute bottom-full left-1/2 mb-3 w-[240px] -translate-x-1/2 rounded-[1.5rem] bg-slate-900/95 dark:bg-slate-800/95 backdrop-blur-md p-5 text-[13px] font-medium text-slate-200 opacity-0 shadow-2xl transition-all duration-300 group-hover:opacity-100 z-[100] leading-relaxed scale-90 group-hover:scale-100 origin-bottom border border-white/10 dark:border-white/5">
        <p className="font-black text-white mb-2 border-b border-white/10 pb-2 flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-400" /> {term}
        </p>
        {explanation}
        <div className="absolute top-full left-1/2 -ml-1 border-4 border-transparent border-t-slate-900/95 dark:border-t-slate-800/95" />
      </div>
    </div>
  );
}

function AIAssist({ field, currentValue, context, onResult, className = "" }: { field: string, currentValue?: string, context: string, onResult: (val: string) => void, className?: string }) {
  const [loading, setLoading] = useState(false);
  const handleAssist = async () => {
    setLoading(true);
    const result = await assistField(field, currentValue || "", context);
    onResult(result);
    setLoading(false);
  };
  const hasContent = currentValue && currentValue.trim().length > 0;
  return (
    <button onClick={handleAssist} disabled={loading} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-black hover:bg-blue-100 dark:hover:bg-blue-800/50 transition-all active:scale-95 disabled:opacity-50 border border-transparent dark:border-blue-800/30 ${className}`}>
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : (hasContent ? <Sparkles className="w-3.5 h-3.5" /> : <Wand2 className="w-3.5 h-3.5" />)}
      {loading ? 'Generating...' : (hasContent ? 'Refine with AI' : 'Draft with AI')}
    </button>
  );
}

function StepIndicator({ currentStep, onStepClick }: { currentStep: number, onStepClick: (s: number) => void }) {
  const steps = [
    { n: 1, label: 'Basics' }, { n: 2, label: 'Design' }, { n: 3, label: 'Features' }, 
    { n: 4, label: 'Tech Stack' }, { n: 5, label: 'Data Model' }, { n: 6, label: 'Generate' },
  ];
  return (
    <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-2xl border border-slate-200 dark:border-slate-700 transition-colors">
      {steps.map((s) => (
        <button key={s.n} onClick={() => onStepClick(s.n)} className={`px-4 py-2 rounded-xl text-xs font-black transition-all duration-300 ${currentStep === s.n ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'}`}>
          {s.label}
        </button>
      ))}
    </div>
  );
}

function MultiSelectGroup({ title, options, selected, onChange, icon: Icon }: { title: string, options: string[], selected: string[], onChange: (vals: string[]) => void, icon?: any }) {
  const toggle = (val: string) => {
    if (selected.includes(val)) {
      onChange(selected.filter(s => s !== val));
    } else {
      onChange([...selected, val]);
    }
  };
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 ml-1">
        {Icon && <Icon className="w-4 h-4 text-blue-500" />}
        <label className="text-sm font-black text-slate-700 dark:text-slate-300 uppercase tracking-wider">{title}</label>
      </div>
      <div className="flex flex-wrap gap-2 p-4 bg-slate-100 dark:bg-black/40 rounded-3xl border border-transparent dark:border-slate-800 min-h-[80px]">
        {options.map(opt => {
          const isSelected = selected.includes(opt);
          return (
            <button key={opt} onClick={() => toggle(opt)} className={`px-4 py-2 rounded-2xl text-[11px] font-black transition-all border-2 ${isSelected ? 'bg-blue-600 border-blue-600 text-white shadow-lg' : 'bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700 text-slate-500 hover:border-blue-400'}`}>
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Single-select button group
function SingleSelectGroup({ title, options, selected, onChange, icon: Icon, description }: { title: string, options: string[], selected: string, onChange: (val: string) => void, icon?: any, description?: string }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-1 ml-1">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-4 h-4 text-blue-500" />}
          <label className="text-sm font-black text-slate-700 dark:text-slate-300 uppercase tracking-wider">{title}</label>
        </div>
        {description && <p className="text-[10px] text-slate-400 font-medium">{description}</p>}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {options.map(opt => {
          const isSelected = selected === opt;
          return (
            <button 
              key={opt} 
              onClick={() => onChange(opt)} 
              className={`px-4 py-3 rounded-2xl text-[11px] font-black transition-all border-2 text-center leading-tight ${
                isSelected 
                  ? 'bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-500/20' 
                  : 'bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800 text-slate-500 hover:border-blue-400 dark:hover:border-blue-900'
              }`}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Step1Basic({ spec, updateSpec }: { spec: TechSpec, updateSpec: any }) {
  const appTypes = ['RWD Responsive Web App', 'Website (Brand / Landing)', 'Mobile App (PWA)', 'Admin Dashboard', 'SaaS Product', 'AI Core Tool'];
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
      <div className="space-y-3">
        <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
          Project Basics <Settings className="w-8 h-8 text-blue-500" />
        </h2>
        <p className="text-lg text-slate-500 dark:text-slate-400 font-medium italic">Define the soul of your app so the AI understands your vision.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-3">
          <div className="flex justify-between items-center px-1">
            <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Project Name</label>
            <AIAssist field="Project Name" currentValue={spec.basic.name} context={`Project type: ${spec.basic.type}`} onResult={(val) => updateSpec('basic', { ...spec.basic, name: val })} />
          </div>
          <input type="text" placeholder="e.g. Smart Fitness Coach, Community Market..." className="w-full px-5 py-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-black focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900/30 outline-none transition-all dark:text-white font-bold" value={spec.basic.name} onChange={(e) => updateSpec('basic', { ...spec.basic, name: e.target.value })} />
        </div>
        <div className="space-y-3">
          <label className="text-sm font-bold text-slate-700 dark:text-slate-300 ml-1">Application Type</label>
          <div className="relative group">
            <select className="w-full px-5 py-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-black appearance-none font-bold text-slate-700 dark:text-slate-200 transition-all cursor-pointer focus:ring-4 focus:ring-blue-100 outline-none" value={spec.basic.type} onChange={(e) => updateSpec('basic', { ...spec.basic, type: e.target.value })}>
              {appTypes.map(type => <option key={type} value={type} className="dark:bg-slate-900">{type}</option>)}
            </select>
            <ChevronDown className="absolute right-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none group-hover:text-blue-500 transition-colors" />
          </div>
        </div>
        <div className="space-y-3 md:col-span-2">
          <div className="flex justify-between items-center px-1">
            <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Project Summary & Goals</label>
            <AIAssist field="Project Summary" currentValue={spec.basic.description} context={`Name: ${spec.basic.name}, Type: ${spec.basic.type}`} onResult={(val) => updateSpec('basic', { ...spec.basic, description: val })} />
          </div>
          <textarea rows={5} placeholder="What problem does it solve? Who are the users?" className="w-full px-5 py-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-black focus:ring-4 focus:ring-blue-100 dark:focus:ring-blue-900/30 outline-none transition-all resize-none dark:text-white font-medium" value={spec.basic.description} onChange={(e) => updateSpec('basic', { ...spec.basic, description: e.target.value })} />
        </div>
      </div>
    </div>
  );
}

function Step2Design({ spec, updateSpec }: { spec: TechSpec, updateSpec: any }) {
  const setDesign = <K extends keyof TechSpec['design']>(key: K, val: TechSpec['design'][K]) => {
    updateSpec('design', { ...spec.design, [key]: val });
  };
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
      <div className="space-y-3">
        <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
          UI Design Spec <Palette className="w-8 h-8 text-indigo-500" />
        </h2>
        <p className="text-lg text-slate-500 dark:text-slate-400 font-medium italic">Pick tags to define the visual tone — we'll turn them into precise UI instructions.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        <MultiSelectGroup icon={Sparkles} title="Design Style" options={DESIGN_OPTIONS.styles} selected={spec.design.styles} onChange={(vals) => setDesign('styles', vals)} />
        <MultiSelectGroup icon={Palette} title="Theme Support" options={DESIGN_OPTIONS.themes} selected={spec.design.themes} onChange={(vals) => setDesign('themes', vals)} />
        <MultiSelectGroup icon={Smartphone} title="Mobile Layout" options={DESIGN_OPTIONS.mobileLayouts} selected={spec.design.mobileLayouts} onChange={(vals) => setDesign('mobileLayouts', vals)} />
        <MultiSelectGroup icon={Monitor} title="Desktop Layout" options={DESIGN_OPTIONS.desktopLayouts} selected={spec.design.desktopLayouts} onChange={(vals) => setDesign('desktopLayouts', vals)} />
      </div>
    </div>
  );
}

function Step3Features({ spec, updateSpec }: { spec: TechSpec, updateSpec: any }) {
  const addFeature = () => {
    const newFeature: Module = { id: crypto.randomUUID(), name: '', description: '', dependencies: [], constraints: '' };
    updateSpec('features', [newFeature, ...spec.features]);
  };
  const removeFeature = (id: string) => updateSpec('features', spec.features.filter(f => f.id !== id));
  const updateFeature = (id: string, updates: Partial<Module>) => updateSpec('features', spec.features.map(f => f.id === id ? { ...f, ...updates } : f));

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div className="space-y-3">
          <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3"><Layers className="w-8 h-8 text-blue-500" /> Feature Modules</h2>
        </div>
        <button onClick={addFeature} className="bg-blue-600 text-white px-8 py-3 rounded-2xl flex items-center gap-2 font-black hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20 active:scale-95"><Plus className="w-5 h-5" /> Add Module</button>
      </header>
      <div className="space-y-10">
        {spec.features.map((feature) => (
          <div key={feature.id} className="group relative p-8 bg-white dark:bg-black/40 border border-slate-200 dark:border-slate-800 rounded-[2.5rem] shadow-sm border-l-[12px] border-l-blue-500 animate-in slide-in-from-top-4">
            <button onClick={() => removeFeature(feature.id)} className="absolute top-6 right-6 p-2 text-slate-300 hover:text-red-500 rounded-full transition-all"><X className="w-6 h-6" /></button>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
              <div className="space-y-6">
                <div className="space-y-2">
                  <div className="flex justify-between items-center px-1">
                    <label className="text-xs font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest">Module Name</label>
                    <AIAssist field="Module Name" currentValue={feature.name} context={`Project: ${spec.basic.name}`} onResult={(val) => updateFeature(feature.id, { name: val })} />
                  </div>
                  <input placeholder="e.g. User Authentication" className="w-full font-black text-2xl text-slate-800 dark:text-white bg-transparent border-b-2 border-slate-100 dark:border-slate-800 focus:border-blue-500 outline-none py-1" value={feature.name} onChange={(e) => updateFeature(feature.id, { name: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center px-1">
                    <label className="text-xs font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest">Detailed Description</label>
                    <AIAssist field="Detailed feature logic" currentValue={feature.description} context={`Module: ${feature.name}, Project goal: ${spec.basic.description}`} onResult={(val) => updateFeature(feature.id, { description: val })} />
                  </div>
                  <textarea rows={4} placeholder="Describe the operational logic..." className="w-full text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-black/60 p-5 rounded-3xl border-0 focus:ring-2 focus:ring-blue-500 outline-none transition-all resize-none shadow-inner" value={feature.description} onChange={(e) => updateFeature(feature.id, { description: e.target.value })} />
                </div>
              </div>
              <div className="space-y-6">
                <div className="space-y-3">
                   <label className="text-xs font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest ml-1">Dependencies (multi-select)</label>
                   <div className="flex flex-wrap gap-2 p-4 bg-slate-50 dark:bg-black/60 rounded-3xl border border-transparent dark:border-slate-800 min-h-[120px]">
                      {FIXED_DEPENDENCIES.concat(spec.features.filter(f => f.id !== feature.id).map(f => f.name)).map(item => {
                         const isSelected = feature.dependencies.includes(item);
                         return (
                           <button key={item} onClick={() => {
                             const next = isSelected ? feature.dependencies.filter(n => n !== item) : [...feature.dependencies, item];
                             updateFeature(feature.id, { dependencies: next });
                           }} className={`px-3 py-1.5 rounded-xl text-[10px] font-black border transition-all ${isSelected ? 'bg-blue-600 border-blue-600 text-white shadow-md' : 'bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700 text-slate-500'}`}>{item}</button>
                         );
                      })}
                   </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center px-1">
                    <label className="text-xs font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest">Constraints & Validation</label>
                    <AIAssist field="Constraints and validation rules" currentValue={feature.constraints} context={`Module: ${feature.name}, Description: ${feature.description}`} onResult={(val) => updateFeature(feature.id, { constraints: val })} />
                  </div>
                  <textarea rows={4} placeholder="Rules and input validation..." className="w-full text-sm font-mono text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-black/60 p-5 rounded-3xl border-0 focus:ring-2 focus:ring-blue-500 outline-none transition-all resize-none shadow-inner" value={feature.constraints} onChange={(e) => updateFeature(feature.id, { constraints: e.target.value })} />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Step4Tech({ spec, updateSpec }: { spec: TechSpec, updateSpec: any }) {
  const setTech = <K extends keyof TechSpec['techStack']>(key: K, val: TechSpec['techStack'][K]) => {
    let nextStack = { ...spec.techStack, [key]: val };
    
    // Auto-config: when picking a frontend framework, suggest a matching UI library
    if (key === 'frontend' && UI_MAPPING[val as string]) {
      nextStack.ui = UI_MAPPING[val as string];
    }

    updateSpec('techStack', nextStack);
  };

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
      <div className="space-y-3">
        <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
          <Monitor className="w-8 h-8 text-blue-500" /> Tech Architecture
        </h2>
        <p className="text-lg text-slate-500 dark:text-slate-400 font-medium italic">Pick one core technology per category. AI will tie them into best-practice implementation guidance.</p>
      </div>

      <div className="grid grid-cols-1 gap-12">
        <SingleSelectGroup 
          title="Frontend Framework" 
          description="Defines the rendering engine and routing model."
          icon={Code2}
          options={TECH_OPTIONS.frontend} 
          selected={spec.techStack.frontend} 
          onChange={(val) => setTech('frontend', val)} 
        />
        
        <SingleSelectGroup 
          title="UI Library" 
          description="Auto-suggested based on your frontend framework choice."
          icon={LayoutGrid}
          options={TECH_OPTIONS.ui} 
          selected={spec.techStack.ui} 
          onChange={(val) => setTech('ui', val)} 
        />

        <SingleSelectGroup 
          title="Backend (API)" 
          description="Core business logic and API service implementation."
          icon={Server}
          options={TECH_OPTIONS.api} 
          selected={spec.techStack.api} 
          onChange={(val) => setTech('api', val)} 
        />

        <SingleSelectGroup 
          title="Database / BaaS" 
          description="Persistent storage layer and cloud backend services."
          icon={Database}
          options={TECH_OPTIONS.database} 
          selected={spec.techStack.database} 
          onChange={(val) => setTech('database', val)} 
        />

        <SingleSelectGroup 
          title="Infrastructure" 
          description="Deployment environment and cloud compute provider."
          icon={Globe}
          options={TECH_OPTIONS.infrastructure} 
          selected={spec.techStack.infrastructure} 
          onChange={(val) => setTech('infrastructure', val)} 
        />
      </div>
    </div>
  );
}

function Step5Schema({ spec, updateSpec }: { spec: TechSpec, updateSpec: any }) {
  const addEntity = () => updateSpec('dataSchema', [{ id: crypto.randomUUID(), name: '', fields: [] }, ...spec.dataSchema]);
  const removeEntity = (id: string) => updateSpec('dataSchema', spec.dataSchema.filter(e => e.id !== id));
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
       <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3"><Database className="w-8 h-8 text-emerald-500" /> Data Schema</h2>
        <button onClick={addEntity} className="bg-emerald-600 text-white px-8 py-3 rounded-2xl flex items-center gap-2 font-black hover:bg-emerald-700 transition-all shadow-emerald-500/20 active:scale-95"><Plus className="w-5 h-5" /> Add Entity</button>
      </header>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {spec.dataSchema.map((entity) => (
          <div key={entity.id} className="p-8 bg-white dark:bg-black/40 border border-slate-200 dark:border-slate-800 rounded-[2.5rem] space-y-6 shadow-sm border-l-[12px] border-l-emerald-500 animate-in slide-in-from-top-4">
            <div className="flex justify-between items-center">
              <div className="flex-1 space-y-1">
                 <label className="text-[10px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest">Table Name</label>
                 <input placeholder="e.g. users, orders" className="w-full font-black text-slate-900 dark:text-white text-2xl border-b-2 border-slate-100 dark:border-slate-700 focus:border-emerald-500 outline-none py-1 bg-transparent" value={entity.name} onChange={(e) => updateSpec('dataSchema', spec.dataSchema.map(ent => ent.id === entity.id ? { ...ent, name: e.target.value } : ent))} />
              </div>
              <button onClick={() => removeEntity(entity.id)} className="p-2 text-slate-300 hover:text-red-500 transition-all"><Trash2 className="w-6 h-6" /></button>
            </div>
            <textarea rows={5} placeholder="Field definitions: id (UUID), title (String)..." className="w-full text-sm font-mono text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-black/60 p-5 rounded-3xl border-0 focus:ring-2 focus:ring-emerald-500 outline-none transition-all resize-none shadow-inner" />
          </div>
        ))}
      </div>
    </div>
  );
}

function Step6Preview({ spec, refinedMarkdown, isRefining, onRefine }: { spec: TechSpec, refinedMarkdown: string | null, isRefining: boolean, onRefine: () => void }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(refinedMarkdown || JSON.stringify(spec, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-6 duration-700 pb-12 transition-all">
      <header className="flex flex-col xl:flex-row xl:items-end justify-between gap-6">
        <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3"><FileText className="w-8 h-8 text-blue-600" /> Spec Summary</h2>
        <div className="flex flex-wrap gap-3">
          <button onClick={copy} className="px-6 py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-2xl font-bold flex items-center gap-2 hover:bg-slate-200 transition-all shadow-sm">{copied ? 'Copied!' : 'Copy Spec'} <Save className="w-5 h-5" /></button>
          {!refinedMarkdown && <button onClick={onRefine} disabled={isRefining} className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl font-black flex items-center gap-2 hover:shadow-2xl transition-all disabled:opacity-50 shadow-lg shadow-blue-500/30">{isRefining ? 'Analyzing...' : 'Deep Refine with AI'} <Sparkles className="w-5 h-5" /></button>}
        </div>
      </header>
      <div className="bg-slate-950 rounded-[3rem] p-8 md:p-14 overflow-hidden min-h-[600px] border-[12px] border-slate-900 shadow-2xl relative shadow-blue-900/10">
        <div className="absolute top-4 right-8 flex gap-2">
           <div className="w-3 h-3 rounded-full bg-red-500/50 shadow-lg shadow-red-500/20"></div>
           <div className="w-3 h-3 rounded-full bg-yellow-500/50 shadow-lg shadow-yellow-500/20"></div>
           <div className="w-3 h-3 rounded-full bg-green-500/50 shadow-lg shadow-green-500/20"></div>
        </div>
        {isRefining ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-8 py-24">
            <div className="relative">
              <div className="w-24 h-24 border-[12px] border-blue-500/10 border-t-blue-500 rounded-full animate-spin"></div>
              <Sparkles className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-blue-400 w-10 h-10 animate-pulse" />
            </div>
            <p className="text-2xl font-black text-slate-200 tracking-tight">AI is drafting your development blueprint...</p>
          </div>
        ) : (
          <div className="prose prose-invert max-w-none text-slate-400 font-mono text-sm leading-relaxed whitespace-pre-wrap selection:bg-blue-500/30">
            {refinedMarkdown || `# Project: ${spec.basic.name || 'Untitled'}\n## Type: ${spec.basic.type}\n\n### 🎯 Vision\n${spec.basic.description || 'No description'}\n\n### 🎨 UI Spec\n- Style: ${spec.design.styles.join(', ')}\n- Theme: ${spec.design.themes.join(', ')}\n- Layout: ${spec.design.mobileLayouts.concat(spec.design.desktopLayouts).join(', ')}\n\n### 🛠️ Tech Stack\n- Frontend: ${spec.techStack.frontend}\n- UI: ${spec.techStack.ui}\n- API: ${spec.techStack.api}\n- Database: ${spec.techStack.database}\n- Infrastructure: ${spec.techStack.infrastructure}\n\n💡 Click "Deep Refine with AI" to generate the full document.`}
          </div>
        )}
      </div>
    </div>
  );
}
