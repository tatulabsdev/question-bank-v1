import { useState, useEffect, useCallback } from "react";

// ── API helper ───────────────────────────────────────────────────────────────
function mkApi(base, key) {
  const h = { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" };
  const u = (t, q = "") => `${base.replace(/\/$/, "")}/rest/v1/${t}${q}`;
  const chk = async r => { if (!r.ok) { const t = await r.text(); throw new Error(t); } return r; };
  return {
    get:    (t,q="")  => fetch(u(t,q),{headers:h}).then(chk).then(r=>r.json()),
    upsert: (t,d)     => fetch(u(t),{method:"POST",headers:{...h,Prefer:"return=representation,resolution=merge-duplicates"},body:JSON.stringify(Array.isArray(d)?d:[d])}).then(chk).then(r=>r.json()),
    patch:  (t,f,v,d) => fetch(u(t,`?${f}=eq.${encodeURIComponent(v)}`),{method:"PATCH",headers:{...h,Prefer:"return=representation"},body:JSON.stringify(d)}).then(chk).then(r=>r.json()),
    del:    (t,f,v)   => fetch(u(t,`?${f}=eq.${encodeURIComponent(v)}`),{method:"DELETE",headers:h}).then(chk),
  };
}

// ── Constants ────────────────────────────────────────────────────────────────
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,"").slice(0,50);
const uid  = (p,n) => `${p}_${slug(n)}_${Date.now().toString(36)}`;

const STATUS_COLORS = {
  deep_dived:"bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
  pass1_mapped_only:"bg-amber-500/20 text-amber-400 border border-amber-500/30",
  not_started:"bg-gray-600/30 text-gray-400 border border-gray-600/30",
  not_applicable:"bg-red-500/20 text-red-400 border border-red-500/30",
};
const COURSE_TYPE_META = {
  foundation_school:  {label:"Foundation — School (Cl 6-12)",   color:"bg-blue-500/20 text-blue-400",   icon:"🏫"},
  foundation_degree:  {label:"Foundation — Degree (Competitive)",color:"bg-violet-500/20 text-violet-400",icon:"🎓"},
  foundation_pg:      {label:"Foundation — PG / PhD",           color:"bg-cyan-500/20 text-cyan-400",   icon:"🔬"},
  foundation_foreign: {label:"Foundation — Foreign Study",      color:"bg-teal-500/20 text-teal-400",   icon:"✈️"},
  rush:               {label:"Rush Course (Exam deadline)",      color:"bg-red-500/20 text-red-400",     icon:"⚡"},
  seasonal:           {label:"Seasonal Offer",                   color:"bg-pink-500/20 text-pink-400",   icon:"🎉"},
};
const UNIT_TYPE_COLORS = {
  learn:"bg-blue-900/40 text-blue-300", practice:"bg-indigo-900/40 text-indigo-300",
  pyq_check:"bg-purple-900/40 text-purple-300", revision:"bg-amber-900/40 text-amber-300",
  assessment:"bg-red-900/40 text-red-300", crossover:"bg-emerald-900/40 text-emerald-300",
};
const CATEGORIES  = ["central_govt","state_govt","banking","defence_paramilitary","railway","academic_entrance_ug","academic_entrance_pg","academic_entrance_phd","k12_olympiad","k12_scholarship","professional_cert","foreign_study","language_proficiency","design_creative","not_applicable"];
const FREQ_TYPES  = ["annual","biannual","irregular_vacancy_driven","every_2_3_years","one_time_notification","ongoing_rolling"];
const MODES       = ["online_cbt","offline_omr","descriptive","hybrid"];
const SUBJ_GROUPS = ["quant","reasoning","english","gk","data_interpretation","technical","computer","language","other"];
const UNIT_TYPES  = ["learn","practice","pyq_check","revision","assessment","crossover"];

// ── Shared UI atoms ──────────────────────────────────────────────────────────
const Btn = ({children,onClick,variant="primary",disabled,small,className=""}) => {
  const sz = small ? "px-3 py-1 text-xs rounded" : "px-4 py-2 text-sm rounded-md";
  const v  = {primary:"bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40",secondary:"bg-gray-700 hover:bg-gray-600 text-gray-200",danger:"bg-red-700 hover:bg-red-600 text-white",ghost:"bg-transparent hover:bg-gray-800 text-gray-400 hover:text-gray-200"};
  return <button onClick={onClick} disabled={disabled} className={`${sz} font-medium transition-colors ${v[variant]||v.primary} ${className}`}>{children}</button>;
};
const Field  = ({label,children,hint}) => <div className="flex flex-col gap-1"><label className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</label>{children}{hint&&<span className="text-xs text-gray-600">{hint}</span>}</div>;
const Input  = p => <input {...p} className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-indigo-500 w-full placeholder-gray-600"/>;
const Textarea=p => <textarea {...p} rows={3} className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-indigo-500 w-full placeholder-gray-600 resize-y"/>;
const Sel    = ({children,...p}) => <select {...p} className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-100 focus:outline-none focus:border-indigo-500 w-full">{children}</select>;
const Tog    = ({label,checked,onChange}) => <label className="flex items-center gap-2 cursor-pointer select-none"><div onClick={()=>onChange(!checked)} className={`w-9 h-5 rounded-full flex items-center px-0.5 transition-colors ${checked?"bg-indigo-600":"bg-gray-700"}`}><div className={`w-4 h-4 rounded-full bg-white shadow transition-transform ${checked?"translate-x-4":"translate-x-0"}`}/></div><span className="text-sm text-gray-300">{label}</span></label>;
const Modal  = ({title,onClose,children,wide}) => <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"><div className={`bg-gray-900 border border-gray-800 rounded-xl shadow-2xl flex flex-col ${wide?"w-full max-w-3xl":"w-full max-w-xl"} max-h-[90vh]`}><div className="flex items-center justify-between px-5 py-4 border-b border-gray-800 shrink-0"><h3 className="text-base font-semibold text-white">{title}</h3><button onClick={onClose} className="text-gray-500 hover:text-gray-200 text-xl">×</button></div><div className="overflow-y-auto p-5 flex flex-col gap-4">{children}</div></div></div>;
const Toast  = ({msg,type}) => <div className={`fixed bottom-4 right-4 z-[100] px-4 py-3 rounded-lg shadow-xl text-sm font-medium ${type==="error"?"bg-red-900 text-red-200":"bg-emerald-900 text-emerald-200"}`}>{type==="error"?"⚠ ":"✓ "}{msg}</div>;
const Badge  = ({label,cls}) => <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${cls}`}>{label}</span>;
const TabBtn = ({id,active,label,onClick}) => <button onClick={onClick} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${active?"border-indigo-500 text-white":"border-transparent text-gray-500 hover:text-gray-300"}`}>{label}</button>;

// ── EXAM FORMS ───────────────────────────────────────────────────────────────
function ExamForm({initial={},onSave,onClose}){
  const [d,setD]=useState({exam_id:"",exam_name:"",conducting_body:"",category:"central_govt",qualification_level:"graduate",frequency_type:"annual",research_status:"not_started",source_file:"",official_url:"",difficulty_score:"",application_fee_gen:"",is_active:true,notes:"",syllabus_notes:"",...initial});
  const set=k=>e=>setD(p=>({...p,[k]:e.target?e.target.value:e}));
  const autoId=()=>{ if(!d.exam_id&&d.exam_name) setD(p=>({...p,exam_id:slug(p.exam_name)})); };
  return <>
    <div className="grid grid-cols-2 gap-3">
      <Field label="Exam Name *"><Input value={d.exam_name} onChange={set("exam_name")} onBlur={autoId} placeholder="e.g. SSC CGL"/></Field>
      <Field label="Exam ID *" hint="auto-filled; lowercase underscores"><Input value={d.exam_id} onChange={set("exam_id")} placeholder="ssc_cgl"/></Field>
      <Field label="Conducting Body"><Input value={d.conducting_body} onChange={set("conducting_body")}/></Field>
      <Field label="Official URL"><Input value={d.official_url} onChange={set("official_url")} placeholder="https://..."/></Field>
      <Field label="Category"><Sel value={d.category} onChange={set("category")}>{CATEGORIES.map(c=><option key={c} value={c}>{c}</option>)}</Sel></Field>
      <Field label="Qualification Level"><Input value={d.qualification_level} onChange={set("qualification_level")} placeholder="graduate"/></Field>
      <Field label="Frequency"><Sel value={d.frequency_type} onChange={set("frequency_type")}>{FREQ_TYPES.map(f=><option key={f} value={f}>{f}</option>)}</Sel></Field>
      <Field label="Research Status"><Sel value={d.research_status} onChange={set("research_status")}>{["not_started","pass1_mapped_only","deep_dived","not_applicable"].map(s=><option key={s} value={s}>{s}</option>)}</Sel></Field>
      <Field label="Difficulty (1-10)"><Input type="number" min="1" max="10" value={d.difficulty_score} onChange={set("difficulty_score")}/></Field>
      <Field label="App. Fee ₹ (General)"><Input type="number" value={d.application_fee_gen} onChange={set("application_fee_gen")}/></Field>
      <Field label="Source File"><Input value={d.source_file} onChange={set("source_file")}/></Field>
      <div className="flex items-end pb-1"><Tog label="Active" checked={d.is_active} onChange={v=>setD(p=>({...p,is_active:v}))}/></div>
    </div>
    <Field label="Notes"><Textarea value={d.notes} onChange={set("notes")}/></Field>
    <Field label="Syllabus Notes"><Textarea value={d.syllabus_notes} onChange={set("syllabus_notes")}/></Field>
    <div className="flex justify-end gap-2 pt-2"><Btn variant="secondary" onClick={onClose}>Cancel</Btn><Btn onClick={()=>onSave(d)} disabled={!d.exam_id||!d.exam_name}>Save Exam</Btn></div>
  </>;
}

function TierForm({examId,initial={},onSave,onClose}){
  const [d,setD]=useState({tier_id:"",tier_name:"",tier_order:1,is_qualifying:false,total_questions:"",total_marks:"",duration_minutes:"",practice_duration_minutes:"",negative_marking_rate:"",mode:"online_cbt",notes:"",...initial});
  const set=k=>e=>setD(p=>({...p,[k]:e.target?e.target.value:e}));
  const autoId=()=>{ if(!d.tier_id&&d.tier_name) setD(p=>({...p,tier_id:uid(examId,p.tier_name)})); };
  return <>
    <div className="grid grid-cols-2 gap-3">
      <Field label="Tier Name *"><Input value={d.tier_name} onChange={set("tier_name")} onBlur={autoId} placeholder="Prelims / Tier 1 / Phase 1"/></Field>
      <Field label="Order"><Input type="number" min="1" value={d.tier_order} onChange={set("tier_order")}/></Field>
      <Field label="Total Questions"><Input type="number" value={d.total_questions} onChange={set("total_questions")}/></Field>
      <Field label="Total Marks"><Input type="number" value={d.total_marks} onChange={set("total_marks")}/></Field>
      <Field label="Duration (minutes)"><Input type="number" value={d.duration_minutes} onChange={set("duration_minutes")}/></Field>
      <Field label="Practice Duration (min)" hint="Override for rush courses e.g. -10 min"><Input type="number" value={d.practice_duration_minutes} onChange={set("practice_duration_minutes")} placeholder="same as actual"/></Field>
      <Field label="Neg. Marking Rate" hint="0.25, 0.333, 1.0 — blank = none"><Input type="number" step="0.001" value={d.negative_marking_rate} onChange={set("negative_marking_rate")}/></Field>
      <Field label="Mode"><Sel value={d.mode} onChange={set("mode")}>{MODES.map(m=><option key={m} value={m}>{m}</option>)}</Sel></Field>
      <div className="col-span-2"><Tog label="Qualifying only (not merit-deciding)" checked={d.is_qualifying} onChange={v=>setD(p=>({...p,is_qualifying:v}))}/></div>
    </div>
    <Field label="Notes"><Textarea value={d.notes} onChange={set("notes")}/></Field>
    <div className="flex justify-end gap-2 pt-2"><Btn variant="secondary" onClick={onClose}>Cancel</Btn><Btn onClick={()=>onSave({...d,exam_id:examId,tier_id:d.tier_id||uid(examId,d.tier_name)})} disabled={!d.tier_name}>Save Tier</Btn></div>
  </>;
}

function SectionForm({tierId,initial={},onSave,onClose}){
  const [d,setD]=useState({section_id:"",section_name:"",section_order:1,num_questions:"",marks_per_question:1,total_marks:"",time_minutes:"",practice_time_minutes:"",negative_marking_override:"",subject_group:"reasoning",notes:"",...initial});
  const set=k=>e=>setD(p=>({...p,[k]:e.target?e.target.value:e}));
  const calc=()=>{ if(d.num_questions&&d.marks_per_question) setD(p=>({...p,total_marks:+p.num_questions*+p.marks_per_question})); };
  return <>
    <div className="grid grid-cols-2 gap-3">
      <Field label="Section Name *"><Input value={d.section_name} onChange={set("section_name")} placeholder="General Intelligence & Reasoning"/></Field>
      <Field label="Order"><Input type="number" min="1" value={d.section_order} onChange={set("section_order")}/></Field>
      <Field label="Questions"><Input type="number" value={d.num_questions} onChange={set("num_questions")} onBlur={calc}/></Field>
      <Field label="Marks/Question"><Input type="number" step="0.5" value={d.marks_per_question} onChange={set("marks_per_question")} onBlur={calc}/></Field>
      <Field label="Total Marks" hint="Auto-calculated"><Input type="number" value={d.total_marks} onChange={set("total_marks")}/></Field>
      <Field label="Time (min)" hint="Blank = no sectional timer"><Input type="number" value={d.time_minutes} onChange={set("time_minutes")}/></Field>
      <Field label="Practice Time (min)" hint="Rush course override"><Input type="number" value={d.practice_time_minutes} onChange={set("practice_time_minutes")} placeholder="same as actual"/></Field>
      <Field label="Neg. Mark Override" hint="Blank = inherits tier rate"><Input type="number" step="0.001" value={d.negative_marking_override} onChange={set("negative_marking_override")}/></Field>
      <Field label="Subject Group"><Sel value={d.subject_group} onChange={set("subject_group")}>{SUBJ_GROUPS.map(g=><option key={g} value={g}>{g}</option>)}</Sel></Field>
    </div>
    <Field label="Notes"><Textarea value={d.notes} onChange={set("notes")}/></Field>
    <div className="flex justify-end gap-2 pt-2"><Btn variant="secondary" onClick={onClose}>Cancel</Btn><Btn onClick={()=>onSave({...d,tier_id:tierId,section_id:d.section_id||uid(tierId,d.section_name)})} disabled={!d.section_name}>Save Section</Btn></div>
  </>;
}

// ── COURSE FORMS ─────────────────────────────────────────────────────────────
function CourseForm({initial={},exams=[],onSave,onClose}){
  const [d,setD]=useState({
    course_id:"",course_title:"",course_subtitle:"",course_type:"foundation_school",
    target_audience:"",class_level_from:"",class_level_to:"",
    target_exam_ids:[],duration_days:"",daily_hours:1,
    revision_next_day:true,revision_weekend:true,revision_two_weeks:true,
    revision_one_month:true,revision_three_months:false,
    highlight_academic_overlap:true,cross_exam_intelligence:true,
    practice_time_reduction_pct:0,
    price_rupees:"",price_pro_rupees:"",price_ultra_rupees:"",
    free_user_can_buy:true,launch_date:"",expiry_date:"",
    is_active:true,description:"",admin_notes:"",...initial,
    target_exam_ids: initial.target_exam_ids||[],
  });
  const set=k=>e=>setD(p=>({...p,[k]:e.target?e.target.value:e}));
  const autoId=()=>{ if(!d.course_id&&d.course_title) setD(p=>({...p,course_id:slug(p.course_title)})); };
  const toggleExam=id=>setD(p=>({...p,target_exam_ids:p.target_exam_ids.includes(id)?p.target_exam_ids.filter(x=>x!==id):[...p.target_exam_ids,id]}));
  const isRush = d.course_type==="rush";
  const isSchool = d.course_type==="foundation_school";
  return <>
    {/* Identity */}
    <div className="grid grid-cols-2 gap-3">
      <Field label="Course Title *" hint="e.g. Stars to Sainik, SSC Olympics, Vacation Kings"><Input value={d.course_title} onChange={set("course_title")} onBlur={autoId} placeholder="SSC Olympics"/></Field>
      <Field label="Course ID *" hint="auto-filled"><Input value={d.course_id} onChange={set("course_id")} placeholder="ssc_olympics"/></Field>
      <Field label="Course Subtitle / Tagline"><Input value={d.course_subtitle} onChange={set("course_subtitle")} placeholder="60-day full speed exam rush"/></Field>
      <Field label="Course Type"><Sel value={d.course_type} onChange={set("course_type")}>{Object.entries(COURSE_TYPE_META).map(([v,m])=><option key={v} value={v}>{m.icon} {m.label}</option>)}</Sel></Field>
      <Field label="Target Audience"><Input value={d.target_audience} onChange={set("target_audience")} placeholder="Class 9-12 students / Degree Final Year..."/></Field>
      {isSchool&&<><Field label="Class From"><Input type="number" min="1" max="12" value={d.class_level_from} onChange={set("class_level_from")} placeholder="6"/></Field><Field label="Class To"><Input type="number" min="1" max="12" value={d.class_level_to} onChange={set("class_level_to")} placeholder="12"/></Field></>}
    </div>

    {/* Target Exams */}
    <Field label="Target Exams" hint="Which exams this course prepares for">
      <div className="bg-gray-800 border border-gray-700 rounded p-2 max-h-28 overflow-y-auto flex flex-wrap gap-1.5">
        {exams.map(e=>{
          const sel=d.target_exam_ids.includes(e.exam_id);
          return <button key={e.exam_id} onClick={()=>toggleExam(e.exam_id)} className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${sel?"bg-indigo-600 border-indigo-500 text-white":"border-gray-600 text-gray-400 hover:border-gray-500"}`}>{e.exam_name}</button>;
        })}
      </div>
    </Field>

    {/* Schedule */}
    <div className="grid grid-cols-3 gap-3">
      <Field label="Duration (days)"><Input type="number" value={d.duration_days} onChange={set("duration_days")} placeholder="365"/></Field>
      <Field label="Daily Hours"><Input type="number" step="0.5" value={d.daily_hours} onChange={set("daily_hours")} placeholder="1"/></Field>
      {isRush&&<Field label="Time Reduction %" hint="e.g. 17 = ~-10 min on 60-min exam"><Input type="number" min="0" max="40" value={d.practice_time_reduction_pct} onChange={set("practice_time_reduction_pct")}/></Field>}
    </div>

    {/* Revision Schedule */}
    <div>
      <div className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Revision Schedule</div>
      <div className="grid grid-cols-3 gap-2">
        <Tog label="Next Day"    checked={d.revision_next_day}     onChange={v=>setD(p=>({...p,revision_next_day:v}))}/>
        <Tog label="Weekend"     checked={d.revision_weekend}      onChange={v=>setD(p=>({...p,revision_weekend:v}))}/>
        <Tog label="2 Weeks"     checked={d.revision_two_weeks}    onChange={v=>setD(p=>({...p,revision_two_weeks:v}))}/>
        <Tog label="1 Month"     checked={d.revision_one_month}    onChange={v=>setD(p=>({...p,revision_one_month:v}))}/>
        <Tog label="3 Months"    checked={d.revision_three_months} onChange={v=>setD(p=>({...p,revision_three_months:v}))}/>
        <Tog label="Academic Overlap Highlight" checked={d.highlight_academic_overlap} onChange={v=>setD(p=>({...p,highlight_academic_overlap:v}))}/>
        <Tog label="Cross-Exam Intelligence"    checked={d.cross_exam_intelligence}    onChange={v=>setD(p=>({...p,cross_exam_intelligence:v}))}/>
      </div>
    </div>

    {/* Pricing */}
    <div className="grid grid-cols-3 gap-3">
      <Field label="Price ₹ (Full)" hint="Free users pay this"><Input type="number" value={d.price_rupees} onChange={set("price_rupees")} placeholder="499"/></Field>
      <Field label="Price ₹ (Pro)"  hint="Discounted"><Input type="number" value={d.price_pro_rupees} onChange={set("price_pro_rupees")} placeholder="299"/></Field>
      <Field label="Price ₹ (Ultra)"hint="Further discount"><Input type="number" value={d.price_ultra_rupees} onChange={set("price_ultra_rupees")} placeholder="149"/></Field>
    </div>
    <div className="grid grid-cols-3 gap-3">
      <Field label="Launch Date"><Input type="date" value={d.launch_date} onChange={set("launch_date")}/></Field>
      <Field label="Expiry Date" hint="Blank = permanent"><Input type="date" value={d.expiry_date} onChange={set("expiry_date")}/></Field>
      <div className="flex flex-col gap-2 justify-end pb-1">
        <Tog label="Free users can buy" checked={d.free_user_can_buy} onChange={v=>setD(p=>({...p,free_user_can_buy:v}))}/>
        <Tog label="Active" checked={d.is_active} onChange={v=>setD(p=>({...p,is_active:v}))}/>
      </div>
    </div>
    <Field label="Description (shown to students)"><Textarea value={d.description} onChange={set("description")}/></Field>
    <Field label="Admin Notes (internal only)"><Textarea value={d.admin_notes} onChange={set("admin_notes")}/></Field>
    <div className="flex justify-end gap-2 pt-2"><Btn variant="secondary" onClick={onClose}>Cancel</Btn><Btn onClick={()=>onSave(d)} disabled={!d.course_id||!d.course_title}>Save Course</Btn></div>
  </>;
}

function UnitForm({courseId,initial={},topics=[],onSave,onClose}){
  const [d,setD]=useState({unit_id:"",unit_title:"",unit_type:"learn",week_number:1,day_number:"",day_of_week:"",unit_order:1,topic_ids:[],difficulty_levels:[1,2,3,4,5],num_questions:20,estimated_minutes:60,is_academic_crossover:false,cross_exam_tags:[],is_revision_of_week:"",notes:"",...initial,topic_ids:initial.topic_ids||[]});
  const set=k=>e=>setD(p=>({...p,[k]:e.target?e.target.value:e}));
  const togTopic=id=>setD(p=>({...p,topic_ids:p.topic_ids.includes(id)?p.topic_ids.filter(x=>x!==id):[...p.topic_ids,id]}));
  const [topicSearch,setTopicSearch]=useState("");
  const filtered=topics.filter(t=>t.topic_id.includes(topicSearch.toLowerCase())||t.topic_name?.toLowerCase().includes(topicSearch.toLowerCase()));
  return <>
    <div className="grid grid-cols-2 gap-3">
      <Field label="Unit Title *"><Input value={d.unit_title} onChange={set("unit_title")} placeholder="Number System — Day 1"/></Field>
      <Field label="Unit Type"><Sel value={d.unit_type} onChange={set("unit_type")}>{UNIT_TYPES.map(t=><option key={t} value={t}>{t}</option>)}</Sel></Field>
      <Field label="Week #"><Input type="number" min="1" value={d.week_number} onChange={set("week_number")}/></Field>
      <Field label="Day # (absolute)"><Input type="number" min="1" value={d.day_number} onChange={set("day_number")} placeholder="1"/></Field>
      <Field label="Questions"><Input type="number" value={d.num_questions} onChange={set("num_questions")}/></Field>
      <Field label="Est. Minutes"><Input type="number" value={d.estimated_minutes} onChange={set("estimated_minutes")}/></Field>
      {d.unit_type==="revision"&&<Field label="Revision of Week #"><Input type="number" value={d.is_revision_of_week} onChange={set("is_revision_of_week")}/></Field>}
      <div className="flex items-end pb-1"><Tog label="Academic Crossover" checked={d.is_academic_crossover} onChange={v=>setD(p=>({...p,is_academic_crossover:v}))}/></div>
    </div>
    <Field label="Topics Covered" hint={`${d.topic_ids.length} selected`}>
      <Input value={topicSearch} onChange={e=>setTopicSearch(e.target.value)} placeholder="Search topics…" className="mb-2"/>
      <div className="bg-gray-800 border border-gray-700 rounded p-2 max-h-32 overflow-y-auto flex flex-wrap gap-1.5">
        {filtered.slice(0,80).map(t=>{
          const sel=d.topic_ids.includes(t.topic_id);
          return <button key={t.topic_id} onClick={()=>togTopic(t.topic_id)} className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${sel?"bg-indigo-600 border-indigo-500 text-white":"border-gray-600 text-gray-400 hover:border-gray-500"}`}>{t.topic_name||t.topic_id}</button>;
        })}
      </div>
    </Field>
    <Field label="Notes"><Textarea value={d.notes} onChange={set("notes")}/></Field>
    <div className="flex justify-end gap-2 pt-2"><Btn variant="secondary" onClick={onClose}>Cancel</Btn><Btn onClick={()=>onSave({...d,course_id:courseId,unit_id:d.unit_id||uid(courseId,d.unit_title)})} disabled={!d.unit_title}>Save Unit</Btn></div>
  </>;
}

// ── SYLLABUS MAP FORM ─────────────────────────────────────────────────────────
function SyllabusForm({examId,sections,topics,initial={},onSave,onClose}){
  const [d,setD]=useState({map_id:"",topic_id:"",section_id:"",weightage_percent:"",priority:3,notes:"",...initial});
  const set=k=>e=>setD(p=>({...p,[k]:e.target?e.target.value:e}));
  return <>
    <div className="flex flex-col gap-3">
      <Field label="Topic *"><Sel value={d.topic_id} onChange={set("topic_id")}><option value="">— Select topic —</option>{topics.map(t=><option key={t.topic_id} value={t.topic_id}>{t.topic_name} ({t.topic_id})</option>)}</Sel></Field>
      <Field label="Section" hint="Leave blank for exam-level mapping"><Sel value={d.section_id} onChange={set("section_id")}><option value="">— Exam level —</option>{sections.map(s=><option key={s.section_id} value={s.section_id}>{s.section_name}</option>)}</Sel></Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Weightage %"><Input type="number" min="0" max="100" step="0.1" value={d.weightage_percent} onChange={set("weightage_percent")}/></Field>
        <Field label="Priority"><Sel value={d.priority} onChange={set("priority")}>{[1,2,3,4,5].map(p=><option key={p} value={p}>{p} — {["Must-Know","High","Medium","Low","Bonus"][p-1]}</option>)}</Sel></Field>
      </div>
      <Field label="Notes"><Textarea value={d.notes} onChange={set("notes")}/></Field>
    </div>
    <div className="flex justify-end gap-2 pt-2"><Btn variant="secondary" onClick={onClose}>Cancel</Btn><Btn onClick={()=>onSave({...d,exam_id:examId,map_id:d.map_id||uid("map",d.topic_id)})} disabled={!d.topic_id}>Save</Btn></div>
  </>;
}

// ── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App(){
  const [url,setUrl]=useState("");
  const [key,setKey]=useState("");
  const [api,setApi]=useState(null);
  const [appMode,setAppMode]=useState("exams"); // "exams" | "courses"

  // Exam state
  const [exams,setExams]=useState([]);
  const [selExamId,setSelExamId]=useState(null);
  const [tiers,setTiers]=useState([]);
  const [sections,setSections]=useState({});
  const [topics,setTopics]=useState([]);
  const [syllabus,setSyllabus]=useState([]);
  const [examTab,setExamTab]=useState("overview");

  // Course state
  const [courses,setCourses]=useState([]);
  const [selCourseId,setSelCourseId]=useState(null);
  const [units,setUnits]=useState([]);
  const [courseTab,setCourseTab]=useState("overview");
  const [courseSearch,setCourseSearch]=useState("");

  const [examSearch,setExamSearch]=useState("");
  const [modal,setModal]=useState(null);
  const [confirm,setConfirm]=useState(null);
  const [toast,setToast]=useState(null);

  const notify=(msg,type="success")=>{ setToast({msg,type}); setTimeout(()=>setToast(null),3500); };
  const err=e=>notify(String(e.message||e),"error");

  const connect=async()=>{
    if(!url||!key){ notify("Enter Supabase URL and service_role key","error"); return; }
    try{ const a=mkApi(url,key); await a.get("exam_registry","?limit=1"); setApi(a); notify("Connected ✓"); }
    catch(e){ err(e); }
  };

  const loadExams    =useCallback(async()=>{ if(!api) return; try{ setExams(await api.get("exam_registry","?order=exam_name&select=*")); }catch(e){err(e);} },[api]);
  const loadCourses  =useCallback(async()=>{ if(!api) return; try{ setCourses(await api.get("courses","?order=sort_order,course_title&select=*")); }catch(e){err(e);} },[api]);
  const loadTopics   =useCallback(async()=>{ if(!api||topics.length) return; try{ setTopics(await api.get("topics","?select=topic_id,topic_name&order=topic_name")); }catch(e){err(e);} },[api,topics.length]);
  const loadTiers    =useCallback(async(id)=>{ if(!api||!id) return; try{ const t=await api.get("exam_tiers",`?exam_id=eq.${id}&order=tier_order`); setTiers(t); const s={}; await Promise.all(t.map(async ti=>{ s[ti.tier_id]=await api.get("exam_sections",`?tier_id=eq.${ti.tier_id}&order=section_order`); })); setSections(s); }catch(e){err(e);} },[api]);
  const loadSyllabus =useCallback(async(id)=>{ if(!api||!id) return; try{ setSyllabus(await api.get("exam_syllabus_map",`?exam_id=eq.${id}&select=*,exam_sections(section_name),topics(topic_name)&order=section_id,priority`)); }catch(e){err(e);} },[api]);
  const loadUnits    =useCallback(async(id)=>{ if(!api||!id) return; try{ setUnits(await api.get("course_units",`?course_id=eq.${id}&order=week_number,day_number,unit_order`)); }catch(e){err(e);} },[api]);

  useEffect(()=>{ loadExams(); loadCourses(); },[loadExams,loadCourses]);
  useEffect(()=>{ if(selExamId){ loadTiers(selExamId); loadSyllabus(selExamId); } },[selExamId,loadTiers,loadSyllabus]);
  useEffect(()=>{ if(selCourseId) loadUnits(selCourseId); },[selCourseId,loadUnits]);
  useEffect(()=>{ if(modal?.type==="add_syllabus"||modal?.type==="edit_syllabus"||modal?.type==="add_unit"||modal?.type==="edit_unit") loadTopics(); },[modal,loadTopics]);

  const selExam   = exams.find(e=>e.exam_id===selExamId);
  const selCourse = courses.find(c=>c.course_id===selCourseId);
  const filtExams = exams.filter(e=>e.exam_name.toLowerCase().includes(examSearch.toLowerCase())||e.conducting_body?.toLowerCase().includes(examSearch.toLowerCase()));
  const filtCourses= courses.filter(c=>c.course_title.toLowerCase().includes(courseSearch.toLowerCase()));
  const weekGroups = units.reduce((acc,u)=>{ const w=u.week_number||1; if(!acc[w]) acc[w]=[]; acc[w].push(u); return acc; },{});

  // Save helpers
  const saveExam=async d=>{ try{ await api.upsert("exam_registry",{...d,difficulty_score:d.difficulty_score?+d.difficulty_score:null,application_fee_gen:d.application_fee_gen?+d.application_fee_gen:null}); await loadExams(); setSelExamId(d.exam_id); setModal(null); notify("Exam saved"); }catch(e){err(e);} };
  const saveTier=async d=>{ try{ await api.upsert("exam_tiers",{...d,tier_order:+d.tier_order,total_questions:d.total_questions?+d.total_questions:null,total_marks:d.total_marks?+d.total_marks:null,duration_minutes:d.duration_minutes?+d.duration_minutes:null,practice_duration_minutes:d.practice_duration_minutes?+d.practice_duration_minutes:null,negative_marking_rate:d.negative_marking_rate?+d.negative_marking_rate:null}); await loadTiers(selExamId); setModal(null); notify("Tier saved"); }catch(e){err(e);} };
  const saveSection=async d=>{ try{ await api.upsert("exam_sections",{...d,section_order:+d.section_order,num_questions:d.num_questions?+d.num_questions:null,marks_per_question:+d.marks_per_question,total_marks:d.total_marks?+d.total_marks:null,time_minutes:d.time_minutes?+d.time_minutes:null,practice_time_minutes:d.practice_time_minutes?+d.practice_time_minutes:null,negative_marking_override:d.negative_marking_override?+d.negative_marking_override:null}); await loadTiers(selExamId); setModal(null); notify("Section saved"); }catch(e){err(e);} };
  const saveSyllabus=async d=>{ try{ await api.upsert("exam_syllabus_map",{...d,weightage_percent:d.weightage_percent?+d.weightage_percent:null,priority:+d.priority}); await loadSyllabus(selExamId); setModal(null); notify("Saved"); }catch(e){err(e);} };
  const saveCourse=async d=>{ try{ const p={...d,duration_days:d.duration_days?+d.duration_days:null,daily_hours:+d.daily_hours,price_rupees:d.price_rupees?+d.price_rupees:null,price_pro_rupees:d.price_pro_rupees?+d.price_pro_rupees:null,price_ultra_rupees:d.price_ultra_rupees?+d.price_ultra_rupees:null,practice_time_reduction_pct:+d.practice_time_reduction_pct,class_level_from:d.class_level_from?+d.class_level_from:null,class_level_to:d.class_level_to?+d.class_level_to:null,target_exam_ids:d.target_exam_ids,launch_date:d.launch_date||null,expiry_date:d.expiry_date||null}; await api.upsert("courses",p); await loadCourses(); setSelCourseId(d.course_id); setModal(null); notify("Course saved"); }catch(e){err(e);} };
  const saveUnit=async d=>{ try{ await api.upsert("course_units",{...d,week_number:+d.week_number,day_number:d.day_number?+d.day_number:null,num_questions:+d.num_questions,estimated_minutes:+d.estimated_minutes,is_revision_of_week:d.is_revision_of_week?+d.is_revision_of_week:null}); await loadUnits(selCourseId); setModal(null); notify("Unit saved"); }catch(e){err(e);} };

  const doDelete=async()=>{ if(!confirm) return; try{ await api.del(confirm.table,confirm.field,confirm.value); if(confirm.table==="exam_registry"){setSelExamId(null);await loadExams();} else if(confirm.table==="exam_tiers") await loadTiers(selExamId); else if(confirm.table==="exam_sections") await loadTiers(selExamId); else if(confirm.table==="exam_syllabus_map") await loadSyllabus(selExamId); else if(confirm.table==="courses"){setSelCourseId(null);await loadCourses();} else if(confirm.table==="course_units") await loadUnits(selCourseId); setConfirm(null); notify("Deleted"); }catch(e){err(e);} };

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-200 text-sm overflow-hidden">

      {/* TOP BAR */}
      <div className="bg-gray-900 border-b border-gray-800 px-4 py-2.5 flex items-center gap-3 shrink-0">
        <span className="text-white font-bold mr-1">🎓 TryIT Admin</span>
        {api ? <>
          <div className="flex bg-gray-800 rounded-lg p-0.5 gap-0.5">
            {["exams","courses"].map(m=><button key={m} onClick={()=>setAppMode(m)} className={`px-3 py-1 rounded text-xs font-medium transition-colors capitalize ${appMode===m?"bg-indigo-600 text-white":"text-gray-400 hover:text-gray-200"}`}>{m==="exams"?"📋 Exams":"📚 Courses"}</button>)}
          </div>
          <span className="text-emerald-400 text-xs">● {url.replace("https://","").split(".")[0]}</span>
          <span className="text-xs text-gray-600">{exams.length} exams · {courses.length} courses</span>
          <Btn onClick={()=>{setApi(null);setExams([]);setCourses([]);setSelExamId(null);setSelCourseId(null);}} variant="ghost" small>Disconnect</Btn>
        </> : <>
          <input value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://xxxx.supabase.co" className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-xs w-64 focus:outline-none focus:border-indigo-500 text-gray-100 placeholder-gray-600"/>
          <input type="password" value={key} onChange={e=>setKey(e.target.value)} placeholder="service_role key" className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-xs w-56 focus:outline-none focus:border-indigo-500 text-gray-100 placeholder-gray-600"/>
          <Btn onClick={connect} small>Connect</Btn>
        </>}
      </div>

      {!api ? (
        <div className="flex-1 flex items-center justify-center flex-col gap-3 text-gray-600">
          <div className="text-4xl">🔒</div>
          <p>Enter your Supabase URL and <strong className="text-gray-500">service_role</strong> key to continue.</p>
          <p className="text-xs">Run <code className="bg-gray-900 px-1 rounded">exam_admin_schema.sql</code> in Supabase first.</p>
        </div>
      ) : appMode==="exams" ? (
        // ── EXAMS VIEW ──────────────────────────────────────────────────────
        <div className="flex flex-1 overflow-hidden">
          <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
            <div className="p-3 border-b border-gray-800 flex gap-2">
              <input value={examSearch} onChange={e=>setExamSearch(e.target.value)} placeholder="Search…" className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-xs flex-1 focus:outline-none focus:border-indigo-500 text-gray-100 placeholder-gray-600"/>
              <Btn small onClick={()=>setModal({type:"add_exam"})}>+</Btn>
            </div>
            <div className="overflow-y-auto flex-1">
              {filtExams.map(e=>(
                <div key={e.exam_id} onClick={()=>{setSelExamId(e.exam_id);setExamTab("overview");}} className={`px-3 py-2.5 cursor-pointer border-b border-gray-800/50 hover:bg-gray-800/60 transition-colors ${selExamId===e.exam_id?"bg-indigo-950/60 border-l-2 border-l-indigo-500":""}`}>
                  <div className="font-medium text-gray-100 text-xs truncate">{e.exam_name}</div>
                  <div className="flex items-center gap-1 mt-1">
                    <Badge label={e.research_status?.replace(/_/g," ")} cls={STATUS_COLORS[e.research_status]||"bg-gray-700 text-gray-400"}/>
                    {!e.is_active&&<Badge label="inactive" cls="bg-red-500/20 text-red-400"/>}
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 border-t border-gray-800 text-xs text-gray-600 space-y-0.5">
              <div>✅ {exams.filter(e=>e.research_status==="deep_dived").length} deep-dived</div>
              <div>🟡 {exams.filter(e=>e.research_status==="pass1_mapped_only").length} pass-1</div>
              <div>⬜ {exams.filter(e=>e.research_status==="not_started").length} not started</div>
            </div>
          </div>
          <div className="flex-1 overflow-hidden flex flex-col">
            {!selExam ? (
              <div className="flex-1 flex items-center justify-center flex-col gap-2 text-gray-600"><div className="text-3xl">📋</div><p>Select an exam or click <strong className="text-gray-500">+</strong> to add.</p></div>
            ) : <>
              <div className="px-5 py-3 border-b border-gray-800 flex items-center gap-3 shrink-0">
                <div className="flex-1"><h2 className="text-base font-semibold text-white">{selExam.exam_name}</h2><div className="text-xs text-gray-500">{selExam.conducting_body} · {selExam.category?.replace(/_/g," ")} · {selExam.qualification_level}</div></div>
                <Badge label={selExam.research_status?.replace(/_/g," ")} cls={STATUS_COLORS[selExam.research_status]}/>
                <Btn small onClick={()=>setModal({type:"edit_exam",data:selExam})}>Edit</Btn>
                <Btn small variant="danger" onClick={()=>setConfirm({table:"exam_registry",field:"exam_id",value:selExamId,label:selExam.exam_name})}>Delete</Btn>
              </div>
              <div className="border-b border-gray-800 px-5 flex shrink-0">
                <TabBtn id="overview" active={examTab==="overview"} label="Overview" onClick={()=>setExamTab("overview")}/>
                <TabBtn id="tiers"    active={examTab==="tiers"}    label={`Tiers & Sections${tiers.length?" ("+tiers.length+")":""}`} onClick={()=>setExamTab("tiers")}/>
                <TabBtn id="syllabus" active={examTab==="syllabus"} label={`Syllabus Map${syllabus.length?" ("+syllabus.length+")":""}`} onClick={()=>setExamTab("syllabus")}/>
              </div>
              <div className="flex-1 overflow-y-auto p-5">
                {examTab==="overview"&&(
                  <div className="grid grid-cols-2 gap-3 max-w-3xl">
                    {[["Exam ID",selExam.exam_id],["Conducting Body",selExam.conducting_body],["Category",selExam.category?.replace(/_/g," ")],["Qualification",selExam.qualification_level],["Frequency",selExam.frequency_type?.replace(/_/g," ")],["Difficulty",selExam.difficulty_score?selExam.difficulty_score+"/10":"—"],["Fee",selExam.application_fee_gen?"₹"+selExam.application_fee_gen:"—"],["URL",selExam.official_url||"—"],["Source File",selExam.source_file||"—"],["Active",selExam.is_active?"Yes":"No"]].map(([k,v])=>(
                      <div key={k} className="bg-gray-900 rounded-lg p-3 border border-gray-800"><div className="text-xs text-gray-500 mb-1">{k}</div><div className="text-sm text-gray-100 font-medium break-all">{v}</div></div>
                    ))}
                    {selExam.notes&&<div className="col-span-2 bg-gray-900 rounded-lg p-3 border border-gray-800"><div className="text-xs text-gray-500 mb-1">Notes</div><div className="text-sm text-gray-300 whitespace-pre-wrap">{selExam.notes}</div></div>}
                  </div>
                )}
                {examTab==="tiers"&&(
                  <div className="max-w-4xl space-y-4">
                    <Btn onClick={()=>setModal({type:"add_tier"})}>+ Add Tier / Stage</Btn>
                    {tiers.length===0&&<p className="text-gray-600 text-sm py-4">No tiers yet — click "+ Add Tier".</p>}
                    {tiers.map(tier=>(
                      <div key={tier.tier_id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                        <div className="flex items-center px-4 py-3 border-b border-gray-800 bg-gray-800/40">
                          <div className="flex-1"><span className="font-semibold text-white">{tier.tier_name}</span><span className="ml-2 text-xs text-gray-500">#{tier.tier_order}</span>{tier.is_qualifying&&<Badge label="Qualifying only" cls="ml-2 bg-amber-500/20 text-amber-400"/>}</div>
                          <div className="flex items-center gap-3 text-xs text-gray-400 mr-4">
                            {tier.total_questions&&<span>{tier.total_questions}Q</span>}{tier.total_marks&&<span>{tier.total_marks}M</span>}{tier.duration_minutes&&<span>{tier.duration_minutes}min</span>}{tier.practice_duration_minutes&&<span className="text-indigo-400">⚡{tier.practice_duration_minutes}min</span>}{tier.negative_marking_rate!=null&&<span>-{tier.negative_marking_rate}</span>}
                          </div>
                          <div className="flex gap-2"><Btn small variant="secondary" onClick={()=>setModal({type:"edit_tier",data:tier})}>Edit</Btn><Btn small onClick={()=>setModal({type:"add_section",tierId:tier.tier_id})}>+ Section</Btn><Btn small variant="danger" onClick={()=>setConfirm({table:"exam_tiers",field:"tier_id",value:tier.tier_id,label:tier.tier_name})}>✕</Btn></div>
                        </div>
                        {(sections[tier.tier_id]||[]).length===0 ? <div className="px-4 py-3 text-xs text-gray-600 italic">No sections yet.</div> : (
                          <table className="w-full text-xs">
                            <thead><tr className="text-gray-500 border-b border-gray-800"><th className="text-left px-4 py-2">Section</th><th className="text-right px-2 py-2">Q</th><th className="text-right px-2 py-2">M/Q</th><th className="text-right px-2 py-2">Total</th><th className="text-right px-2 py-2">Time</th><th className="text-right px-2 py-2">⚡Practice</th><th className="text-left px-2 py-2">Group</th><th className="text-right px-2 py-2">Neg.</th><th className="px-2 py-2"></th></tr></thead>
                            <tbody>{(sections[tier.tier_id]||[]).map(s=>(
                              <tr key={s.section_id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                                <td className="px-4 py-2 font-medium text-gray-200">{s.section_name}</td>
                                <td className="px-2 py-2 text-right text-gray-300">{s.num_questions??"—"}</td>
                                <td className="px-2 py-2 text-right text-gray-300">{s.marks_per_question??"—"}</td>
                                <td className="px-2 py-2 text-right font-semibold text-gray-200">{s.total_marks??"—"}</td>
                                <td className="px-2 py-2 text-right text-gray-400">{s.time_minutes?s.time_minutes+"m":"—"}</td>
                                <td className="px-2 py-2 text-right text-indigo-400">{s.practice_time_minutes?s.practice_time_minutes+"m":"—"}</td>
                                <td className="px-2 py-2"><Badge label={s.subject_group} cls="bg-indigo-900/40 text-indigo-400"/></td>
                                <td className="px-2 py-2 text-right text-gray-400">{s.negative_marking_override!=null?"-"+s.negative_marking_override:"inherit"}</td>
                                <td className="px-2 py-2 flex gap-1 justify-end"><Btn small variant="ghost" onClick={()=>setModal({type:"edit_section",tierId:tier.tier_id,data:s})}>✎</Btn><Btn small variant="ghost" onClick={()=>setConfirm({table:"exam_sections",field:"section_id",value:s.section_id,label:s.section_name})}>✕</Btn></td>
                              </tr>
                            ))}</tbody>
                          </table>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {examTab==="syllabus"&&(
                  <div className="max-w-4xl">
                    <div className="flex items-center gap-3 mb-4"><Btn onClick={()=>setModal({type:"add_syllabus"})}>+ Map Topic</Btn><span className="text-xs text-gray-500">{syllabus.length} mappings</span></div>
                    {syllabus.length>0&&<table className="w-full text-xs border border-gray-800 rounded-lg overflow-hidden"><thead><tr className="bg-gray-800/60 text-gray-400 text-left"><th className="px-3 py-2">Topic</th><th className="px-3 py-2">Section</th><th className="px-3 py-2 text-right">Weight%</th><th className="px-3 py-2 text-center">Priority</th><th className="px-3 py-2">Notes</th><th className="px-2 py-2"></th></tr></thead>
                    <tbody>{syllabus.map(s=><tr key={s.map_id} className="border-t border-gray-800/50 hover:bg-gray-800/20"><td className="px-3 py-2 font-medium text-gray-200">{s.topics?.topic_name||s.topic_id}</td><td className="px-3 py-2 text-gray-400">{s.exam_sections?.section_name||"—"}</td><td className="px-3 py-2 text-right text-gray-300">{s.weightage_percent??"—"}</td><td className="px-3 py-2 text-center text-gray-400">{s.priority}</td><td className="px-3 py-2 text-gray-600 italic truncate max-w-xs">{s.notes||""}</td><td className="px-2 py-2 flex gap-1 justify-end"><Btn small variant="ghost" onClick={()=>setModal({type:"edit_syllabus",data:s})}>✎</Btn><Btn small variant="ghost" onClick={()=>setConfirm({table:"exam_syllabus_map",field:"map_id",value:s.map_id,label:s.topics?.topic_name})}>✕</Btn></td></tr>)}</tbody></table>}
                  </div>
                )}
              </div>
            </>}
          </div>
        </div>
      ) : (
        // ── COURSES VIEW ─────────────────────────────────────────────────────
        <div className="flex flex-1 overflow-hidden">
          <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
            <div className="p-3 border-b border-gray-800 flex gap-2">
              <input value={courseSearch} onChange={e=>setCourseSearch(e.target.value)} placeholder="Search courses…" className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-xs flex-1 focus:outline-none focus:border-indigo-500 text-gray-100 placeholder-gray-600"/>
              <Btn small onClick={()=>setModal({type:"add_course"})}>+</Btn>
            </div>
            <div className="overflow-y-auto flex-1">
              {filtCourses.map(c=>{
                const meta=COURSE_TYPE_META[c.course_type]||{icon:"📘",color:"bg-gray-700 text-gray-400",label:c.course_type};
                return <div key={c.course_id} onClick={()=>{setSelCourseId(c.course_id);setCourseTab("overview");}} className={`px-3 py-2.5 cursor-pointer border-b border-gray-800/50 hover:bg-gray-800/60 transition-colors ${selCourseId===c.course_id?"bg-indigo-950/60 border-l-2 border-l-indigo-500":""}`}>
                  <div className="font-medium text-gray-100 text-xs truncate">{meta.icon} {c.course_title}</div>
                  <div className="flex items-center gap-1 mt-1"><Badge label={meta.label} cls={meta.color}/>{!c.is_active&&<Badge label="inactive" cls="bg-red-500/20 text-red-400"/>}</div>
                  {c.price_rupees&&<div className="text-xs text-gray-500 mt-0.5">₹{c.price_rupees}{c.price_pro_rupees?` · Pro ₹${c.price_pro_rupees}`:""}</div>}
                </div>;
              })}
              {filtCourses.length===0&&<div className="p-4 text-xs text-gray-600 text-center">No courses yet. Click + to create one.</div>}
            </div>
            <div className="p-3 border-t border-gray-800 text-xs text-gray-600 space-y-0.5">
              {Object.entries(COURSE_TYPE_META).map(([k,v])=>{
                const n=courses.filter(c=>c.course_type===k).length;
                return n>0?<div key={k}>{v.icon} {n} {v.label.split(" — ")[1]||k}</div>:null;
              })}
            </div>
          </div>
          <div className="flex-1 overflow-hidden flex flex-col">
            {!selCourse ? (
              <div className="flex-1 flex items-center justify-center flex-col gap-2 text-gray-600">
                <div className="text-3xl">📚</div>
                <p>Select a course or click <strong className="text-gray-500">+</strong> to create one.</p>
                <p className="text-xs max-w-sm text-center">Foundation courses run year-round. Rush/Seasonal courses have start and expiry dates.</p>
              </div>
            ) : <>
              <div className="px-5 py-3 border-b border-gray-800 flex items-center gap-3 shrink-0">
                <div className="flex-1">
                  <h2 className="text-base font-semibold text-white">{COURSE_TYPE_META[selCourse.course_type]?.icon} {selCourse.course_title}</h2>
                  <div className="text-xs text-gray-500">{selCourse.course_subtitle||selCourse.course_type?.replace(/_/g," ")} · {selCourse.target_audience||""}</div>
                </div>
                {!selCourse.is_active&&<Badge label="Inactive" cls="bg-red-500/20 text-red-400"/>}
                <Btn small onClick={()=>setModal({type:"edit_course",data:selCourse})}>Edit</Btn>
                <Btn small onClick={()=>setModal({type:"add_unit"})}>+ Add Unit</Btn>
                <Btn small variant="danger" onClick={()=>setConfirm({table:"courses",field:"course_id",value:selCourseId,label:selCourse.course_title})}>Delete</Btn>
              </div>
              <div className="border-b border-gray-800 px-5 flex shrink-0">
                <TabBtn id="overview" active={courseTab==="overview"} label="Overview"       onClick={()=>setCourseTab("overview")}/>
                <TabBtn id="plan"     active={courseTab==="plan"}     label={`Weekly Plan${units.length?" ("+units.length+" units)":""}`} onClick={()=>setCourseTab("plan")}/>
                <TabBtn id="pricing"  active={courseTab==="pricing"}  label="Pricing & Access" onClick={()=>setCourseTab("pricing")}/>
              </div>
              <div className="flex-1 overflow-y-auto p-5">
                {courseTab==="overview"&&(
                  <div className="grid grid-cols-2 gap-3 max-w-3xl">
                    {[["Course ID",selCourse.course_id],["Type",selCourse.course_type?.replace(/_/g," ")],["Target Audience",selCourse.target_audience||"—"],["Class Range",selCourse.class_level_from?`Class ${selCourse.class_level_from}–${selCourse.class_level_to}`:"—"],["Duration",selCourse.duration_days?selCourse.duration_days+" days":"—"],["Daily Hours",selCourse.daily_hours+"h/day"],["Time Reduction",selCourse.practice_time_reduction_pct?selCourse.practice_time_reduction_pct+"%":"—"],["Active",selCourse.is_active?"Yes":"No"],["Launch",selCourse.launch_date||"—"],["Expires",selCourse.expiry_date||"Permanent"]].map(([k,v])=>(
                      <div key={k} className="bg-gray-900 rounded-lg p-3 border border-gray-800"><div className="text-xs text-gray-500 mb-1">{k}</div><div className="text-sm text-gray-100 font-medium">{v}</div></div>
                    ))}
                    <div className="bg-gray-900 rounded-lg p-3 border border-gray-800">
                      <div className="text-xs text-gray-500 mb-2">Revision Schedule</div>
                      <div className="flex flex-wrap gap-1">
                        {[["Next Day",selCourse.revision_next_day],["Weekend",selCourse.revision_weekend],["2 Weeks",selCourse.revision_two_weeks],["1 Month",selCourse.revision_one_month],["3 Months",selCourse.revision_three_months],["Academic Overlap",selCourse.highlight_academic_overlap],["Cross-Exam Intel",selCourse.cross_exam_intelligence]].map(([l,v])=><Badge key={l} label={l} cls={v?"bg-emerald-500/20 text-emerald-400":"bg-gray-700 text-gray-600"}/>)}
                      </div>
                    </div>
                    {selCourse.description&&<div className="col-span-2 bg-gray-900 rounded-lg p-3 border border-gray-800"><div className="text-xs text-gray-500 mb-1">Description</div><div className="text-sm text-gray-300 whitespace-pre-wrap">{selCourse.description}</div></div>}
                    {selCourse.target_exam_ids?.length>0&&<div className="col-span-2 bg-gray-900 rounded-lg p-3 border border-gray-800"><div className="text-xs text-gray-500 mb-2">Target Exams</div><div className="flex flex-wrap gap-1">{selCourse.target_exam_ids.map(id=><Badge key={id} label={exams.find(e=>e.exam_id===id)?.exam_name||id} cls="bg-indigo-900/40 text-indigo-400"/>)}</div></div>}
                  </div>
                )}
                {courseTab==="plan"&&(
                  <div className="max-w-4xl">
                    {units.length===0&&<p className="text-gray-600 text-sm py-4">No units yet. Click "+ Add Unit" to build the daily plan.</p>}
                    {Object.entries(weekGroups).sort(([a],[b])=>+a-+b).map(([week,weekUnits])=>(
                      <div key={week} className="mb-5">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-sm font-semibold text-white">Week {week}</h3>
                          <span className="text-xs text-gray-500">{weekUnits.length} units · {weekUnits.reduce((s,u)=>s+(u.estimated_minutes||0),0)} min total</span>
                        </div>
                        <div className="space-y-1.5">
                          {weekUnits.map(u=>(
                            <div key={u.unit_id} className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 hover:border-gray-700 transition-colors">
                              <span className="text-xs w-6 text-center text-gray-600">D{u.day_number||"?"}</span>
                              <Badge label={u.unit_type} cls={UNIT_TYPE_COLORS[u.unit_type]||"bg-gray-700 text-gray-400"}/>
                              <span className="flex-1 text-sm text-gray-200 font-medium truncate">{u.unit_title}</span>
                              {u.is_academic_crossover&&<Badge label="Academic Crossover" cls="bg-emerald-900/40 text-emerald-400"/>}
                              <span className="text-xs text-gray-500">{u.num_questions}Q · {u.estimated_minutes}min</span>
                              <Btn small variant="ghost" onClick={()=>setModal({type:"edit_unit",data:u})}>✎</Btn>
                              <Btn small variant="ghost" onClick={()=>setConfirm({table:"course_units",field:"unit_id",value:u.unit_id,label:u.unit_title})}>✕</Btn>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {courseTab==="pricing"&&(
                  <div className="max-w-2xl space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      {[["Free User Price",selCourse.price_rupees,"bg-gray-900"],["Pro User Price",selCourse.price_pro_rupees,"bg-indigo-950/60"],["Ultra User Price",selCourse.price_ultra_rupees,"bg-violet-950/60"]].map(([l,v,bg])=>(
                        <div key={l} className={`${bg} rounded-xl border border-gray-800 p-4 text-center`}>
                          <div className="text-xs text-gray-500 mb-1">{l}</div>
                          <div className="text-2xl font-bold text-white">{v?`₹${v}`:"—"}</div>
                        </div>
                      ))}
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      {[["Free users can buy",selCourse.free_user_can_buy],["Active",selCourse.is_active],["Launch date",selCourse.launch_date||"Immediate"],["Expiry",selCourse.expiry_date||"Permanent"]].map(([k,v])=>(
                        <div key={k} className="bg-gray-900 rounded-lg p-3 border border-gray-800"><div className="text-xs text-gray-500 mb-1">{k}</div><div className="text-sm font-medium text-gray-100">{typeof v==="boolean"?(v?"Yes":"No"):v}</div></div>
                      ))}
                    </div>
                    {selCourse.admin_notes&&<div className="bg-gray-900 rounded-lg p-3 border border-gray-800"><div className="text-xs text-gray-500 mb-1">Admin Notes</div><div className="text-sm text-gray-300 whitespace-pre-wrap">{selCourse.admin_notes}</div></div>}
                  </div>
                )}
              </div>
            </>}
          </div>
        </div>
      )}

      {/* MODALS */}
      {modal?.type==="add_exam"  &&<Modal title="Add Exam"    onClose={()=>setModal(null)} wide><ExamForm onSave={saveExam} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="edit_exam" &&<Modal title="Edit Exam"   onClose={()=>setModal(null)} wide><ExamForm initial={modal.data} onSave={saveExam} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="add_tier"  &&<Modal title="Add Tier"    onClose={()=>setModal(null)}><TierForm examId={selExamId} onSave={saveTier} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="edit_tier" &&<Modal title="Edit Tier"   onClose={()=>setModal(null)}><TierForm examId={selExamId} initial={modal.data} onSave={saveTier} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="add_section" &&<Modal title="Add Section"  onClose={()=>setModal(null)}><SectionForm tierId={modal.tierId} onSave={saveSection} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="edit_section"&&<Modal title="Edit Section" onClose={()=>setModal(null)}><SectionForm tierId={modal.tierId} initial={modal.data} onSave={saveSection} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="add_syllabus" &&<Modal title="Map Topic"        onClose={()=>setModal(null)}><SyllabusForm examId={selExamId} sections={Object.values(sections).flat()} topics={topics} onSave={saveSyllabus} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="edit_syllabus"&&<Modal title="Edit Topic Map"   onClose={()=>setModal(null)}><SyllabusForm examId={selExamId} sections={Object.values(sections).flat()} topics={topics} initial={modal.data} onSave={saveSyllabus} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="add_course" &&<Modal title="Add Course"    onClose={()=>setModal(null)} wide><CourseForm exams={exams} onSave={saveCourse} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="edit_course"&&<Modal title="Edit Course"   onClose={()=>setModal(null)} wide><CourseForm exams={exams} initial={modal.data} onSave={saveCourse} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="add_unit"  &&<Modal title="Add Course Unit"  onClose={()=>setModal(null)} wide><UnitForm courseId={selCourseId} topics={topics} onSave={saveUnit} onClose={()=>setModal(null)}/></Modal>}
      {modal?.type==="edit_unit" &&<Modal title="Edit Course Unit" onClose={()=>setModal(null)} wide><UnitForm courseId={selCourseId} topics={topics} initial={modal.data} onSave={saveUnit} onClose={()=>setModal(null)}/></Modal>}

      {/* DELETE CONFIRM */}
      {confirm&&<div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"><div className="bg-gray-900 border border-gray-800 rounded-xl p-5 max-w-sm w-full shadow-2xl"><h3 className="font-semibold text-white mb-2">Delete "{confirm.label}"?</h3><p className="text-xs text-gray-400 mb-4">This cannot be undone. Child records (tiers, sections, units) will also be deleted.</p><div className="flex justify-end gap-2"><Btn variant="secondary" onClick={()=>setConfirm(null)}>Cancel</Btn><Btn variant="danger" onClick={doDelete}>Delete</Btn></div></div></div>}
      {toast&&<Toast msg={toast.msg} type={toast.type}/>}
    </div>
  );
}
