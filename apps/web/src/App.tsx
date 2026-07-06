import { useEffect, useMemo, useState, type ComponentType } from "react";
import {
  ArrowLeft, ArrowRight, Bell, BriefcaseBusiness, Building2, Check, ChevronRight,
  CircleDollarSign, Compass, GitCompareArrows, Heart, Home, Map as MapIcon, MapPin,
  LogOut, Search, ShieldCheck, SlidersHorizontal, Sparkles, Trees, UserRound, Users,
} from "lucide-react";
import { fetchCity, fetchExplore, fetchJobs, fetchProfiles } from "./api";
import { AuthDialog } from "./AuthDialog";
import { currentUser, signOut, subscribeToAuth } from "./auth";
import type { CityDetail, CitySummary, ExploreCity, IntentId, JobListing, UserProfile } from "./types";

type View = "intent" | "questions" | "results" | "explore" | "detail" | "tradeoffs" | "saved";
type IconType = ComponentType<{ size?: number; strokeWidth?: number; className?: string }>;

const INTENTS: { id: IntentId; label: string; icon: IconType }[] = [
  { id: "offer", label: "Evaluate a job offer", icon: BriefcaseBusiness },
  { id: "opportunities", label: "Find places with work for me", icon: Search },
  { id: "compare", label: "Compare places", icon: GitCompareArrows },
  { id: "explore", label: "Explore without a plan", icon: Compass },
];

const EMPTY_PROFILE: UserProfile = {
  intent: "explore", role: "", offeredCity: "", housingBudget: 1800,
  placeScale: "open", socialEnergy: "open", greenery: "open",
};

const money = (value: number) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 0,
}).format(value);

function confidence(city: ExploreCity, profile?: CitySummary) {
  if (profile?.score_context.overall_confidence === "source_backed") return "High confidence";
  return city.active_listing_count >= 10 ? "Good job coverage" : "Limited job coverage";
}

function AppHeader({ view, onNavigate, authEmail, onSignIn, onSignOut }: { view: View; onNavigate: (view: View) => void; authEmail: string; onSignIn: () => void; onSignOut: () => void }) {
  return (
    <header className="site-header">
      <button className="wordmark" onClick={() => onNavigate("intent")} aria-label="WSIS home">
        <span>W</span> <strong>wsis</strong>
      </button>
      <nav aria-label="Main navigation">
        <button className={view === "results" ? "active" : ""} onClick={() => onNavigate("results")}>Matches</button>
        <button className={view === "explore" ? "active" : ""} onClick={() => onNavigate("explore")}>Explore</button>
        <button className={view === "tradeoffs" ? "active" : ""} onClick={() => onNavigate("tradeoffs")}>Tradeoffs</button>
        <button className={view === "saved" ? "active" : ""} onClick={() => onNavigate("saved")}>Saved</button>
      </nav>
      <button className="sign-in-button" onClick={authEmail ? onSignOut : onSignIn} aria-label={authEmail ? `Sign out ${authEmail}` : "Sign in to save"}>{authEmail ? <><UserRound size={17}/><span>{authEmail.split("@")[0]}</span><LogOut size={15}/></> : "Sign in to save"}</button>
    </header>
  );
}

function MobileNav({ view, onNavigate }: { view: View; onNavigate: (view: View) => void }) {
  const items: { view: View; label: string; icon: IconType }[] = [
    { view: "results", label: "Matches", icon: Sparkles },
    { view: "explore", label: "Explore", icon: MapIcon },
    { view: "tradeoffs", label: "Tradeoffs", icon: SlidersHorizontal },
    { view: "saved", label: "Saved", icon: Heart },
  ];
  return <nav className="mobile-nav" aria-label="Mobile navigation">{items.map((item) => {
    const Icon = item.icon;
    return <button key={item.view} className={view === item.view ? "active" : ""} onClick={() => onNavigate(item.view)}><Icon size={20}/><span>{item.label}</span></button>;
  })}</nav>;
}

function IntentScreen({ onSelect }: { onSelect: (intent: IntentId) => void }) {
  return <main className="welcome-shell">
    <section className="welcome-copy">
      <p className="brand-name">WSIS</p>
      <h1>Find places where your work and life can fit.</h1>
      <p>Start with the decision in front of you. We’ll show what fits, what doesn’t, and how strong the evidence is.</p>
      <div className="privacy-line"><ShieldCheck size={19}/> Explore first. Sign in only when you want to save.</div>
    </section>
    <section className="intent-panel" aria-labelledby="intent-heading">
      <h2 id="intent-heading">What are you trying to decide?</h2>
      <div className="intent-list">{INTENTS.map((intent) => {
        const Icon = intent.icon;
        return <button key={intent.id} onClick={() => onSelect(intent.id)}><span className="round-icon"><Icon size={24}/></span><strong>{intent.label}</strong><ArrowRight size={20}/></button>;
      })}</div>
    </section>
  </main>;
}

function QuestionsScreen({ profile, cities, onChange, onBack, onComplete }: {
  profile: UserProfile; cities: ExploreCity[]; onChange: (profile: UserProfile) => void;
  onBack: () => void; onComplete: () => void;
}) {
  return <main className="question-page page-width">
    <button className="back-link" onClick={onBack}><ArrowLeft size={18}/> Change goal</button>
    <div className="question-heading"><div><span>Build your situation</span><h1>Give us the useful constraints.</h1></div><p>Nothing is assumed. Skip what you don’t know; every answer stays editable.</p></div>
    <form className="question-form" onSubmit={(event) => { event.preventDefault(); onComplete(); }}>
      <label><span><BriefcaseBusiness size={20}/> Desired role or skill</span><input value={profile.role} onChange={(e) => onChange({...profile, role:e.target.value})} placeholder="Data analyst, product designer, operations…"/></label>
      {profile.intent === "offer" ? <label><span><MapPin size={20}/> Offer city</span><select value={profile.offeredCity} onChange={(e) => onChange({...profile, offeredCity:e.target.value})}><option value="">Choose the offered city</option>{cities.slice(0,150).map(city => <option key={city.place_geoid} value={city.place_geoid}>{city.name}, {city.state_code}</option>)}</select></label> : null}
      <label><span><Home size={20}/> Safe monthly housing payment</span><div className="range-line"><input type="range" min="700" max="5000" step="100" value={profile.housingBudget} onChange={(e) => onChange({...profile,housingBudget:Number(e.target.value)})}/><output>{money(profile.housingBudget)}</output></div></label>
      <fieldset><legend><Building2 size={20}/> What kind of place feels right?</legend><div className="option-grid">{[["major","Major city"],["midsize","Mid-sized city"],["small","Small place"],["open","Open to any"]].map(([value,label]) => <button type="button" className={profile.placeScale===value?"selected":""} onClick={() => onChange({...profile,placeScale:value as UserProfile["placeScale"]})} key={value}>{label}</button>)}</div></fieldset>
      <fieldset><legend><Users size={20}/> How much social energy do you want nearby?</legend><div className="option-grid">{[["quiet","Prefer quiet"],["mix","A mix"],["lively","Prefer lively"],["open","No preference"]].map(([value,label]) => <button type="button" className={profile.socialEnergy===value?"selected":""} onClick={() => onChange({...profile,socialEnergy:value as UserProfile["socialEnergy"]})} key={value}>{label}</button>)}</div></fieldset>
      <fieldset><legend><Trees size={20}/> What kind of green access matters?</legend><div className="option-grid">{[["parks","Everyday parks"],["nature","Weekend nature"],["both","Both"],["open","No preference"]].map(([value,label]) => <button type="button" className={profile.greenery===value?"selected":""} onClick={() => onChange({...profile,greenery:value as UserProfile["greenery"]})} key={value}>{label}</button>)}</div></fieldset>
      <div className="form-actions"><button type="button" className="secondary-button" onClick={onComplete}>Skip remaining</button><button className="primary-button">Show my five places <ArrowRight size={19}/></button></div>
    </form>
  </main>;
}

function LoadingCards() { return <div className="card-grid">{[1,2,3,4,5].map(i => <div className="skeleton-card" key={i}><span/><span/><span/></div>)}</div>; }

function CityCard({ city, profile, rank, onOpen, onSave, saved }: { city: ExploreCity; profile?: CitySummary; rank: number; onOpen:()=>void; onSave:()=>void; saved:boolean }) {
  return <article className="city-card">
    <div className="card-top"><span className="rank">{rank}</span><button className="icon-button" onClick={onSave} aria-label={saved?`Remove ${city.name} from saved`:`Save ${city.name}`}><Heart size={20} fill={saved?"currentColor":"none"}/></button></div>
    <div><p className="city-state">{city.state_code} · {city.active_listing_count} active roles</p><h3>{city.name}</h3></div>
    <div className="fit-summary"><p><Check size={17}/> <span><strong>Why it fits</strong>{profile ? `WSIS score ${profile.overall_score.toFixed(1)} with source-backed evidence.` : "Current early-career roles are present in the covered feed."}</span></p><p><ShieldCheck size={17}/><span><strong>What to verify</strong>{profile ? "Open the city evidence to verify rent, neighborhood, and commute." : "Full affordability and city evidence is still being expanded."}</span></p></div>
    <div className="confidence-row"><span>{confidence(city,profile)}</span><span>Updated {city.latest_listing_date}</span></div>
    <button className="card-link" onClick={onOpen}>Explore city and jobs <ArrowRight size={18}/></button>
  </article>;
}

function ResultsScreen({ profile, cities, profiles, onOpen, onExplore, saved, toggleSaved }: { profile:UserProfile; cities:ExploreCity[]; profiles:CitySummary[]; onOpen:(city:ExploreCity)=>void; onExplore:()=>void; saved:Set<string>; toggleSaved:(city:ExploreCity)=>void }) {
  const profileMap = useMemo(() => new Map(profiles.map(item => [item.slug,item])), [profiles]);
  const picks = useMemo(() => {
    const sorted = [...cities];
    if (profile.intent === "offer" && profile.offeredCity) {
      const offered = sorted.find(city => city.place_geoid===profile.offeredCity);
      return offered ? [offered,...sorted.filter(city=>city.place_geoid!==offered.place_geoid).slice(0,4)] : sorted.slice(0,5);
    }
    return sorted.slice(0,5);
  },[cities,profile.intent,profile.offeredCity]);
  return <main className="content-page page-width">
    <section className="results-hero"><div><p>{profile.intent === "offer" ? "Offer verdict + alternatives" : "Your first five places"}</p><h1>Places where work and life can fit.</h1><span>Based on your explicit answers and currently covered job data—not a universal “best city” list.</span></div><button className="secondary-button" onClick={onExplore}>Explore all covered places</button></section>
    {picks.length ? <div className="card-grid">{picks.map((city,index)=><CityCard key={city.place_geoid} city={city} profile={profileMap.get(city.slug)} rank={index+1} onOpen={()=>onOpen(city)} saved={saved.has(city.place_geoid)} onSave={()=>toggleSaved(city)}/>)}</div> : <LoadingCards/>}
    <aside className="coverage-banner"><ShieldCheck size={23}/><div><strong>Coverage, not certainty</strong><p>Listings are from covered public feeds. “No roles found” never means no jobs exist. Official BLS labor evidence will remain separate from live-listing coverage.</p></div></aside>
  </main>;
}

function GeoPlot({ cities, onOpen }: { cities:ExploreCity[]; onOpen:(city:ExploreCity)=>void }) {
  return <div className="geo-plot" aria-label="Geographic view of job-covered places">{cities.slice(0,80).map(city => {
    const left=Math.max(3,Math.min(97,((city.longitude+125)/59)*100)); const top=Math.max(4,Math.min(94,((49-city.latitude)/25)*100));
    return <button key={city.place_geoid} style={{left:`${left}%`,top:`${top}%`,width:`${Math.max(8,Math.min(22,7+Math.sqrt(city.active_listing_count)))}px`,height:`${Math.max(8,Math.min(22,7+Math.sqrt(city.active_listing_count)))}px`}} title={`${city.name}, ${city.state_code}: ${city.active_listing_count} roles`} onClick={()=>onOpen(city)}><span className="sr-only">{city.name}, {city.state_code}</span></button>;
  })}<span className="map-west">West</span><span className="map-east">East</span></div>;
}

function ExploreScreen({ cities, profiles, onOpen }: { cities:ExploreCity[]; profiles:CitySummary[]; onOpen:(city:ExploreCity)=>void }) {
  const [query,setQuery]=useState(""); const [state,setState]=useState("ALL");
  const states=useMemo(()=>[...new Set(cities.map(city=>city.state_code))].sort(),[cities]);
  const visible=useMemo(()=>cities.filter(city=>(state==="ALL"||city.state_code===state)&&`${city.name} ${city.state_code}`.toLowerCase().includes(query.toLowerCase())).slice(0,60),[cities,query,state]);
  const profileMap=new Map(profiles.map(item=>[item.slug,item]));
  return <main className="content-page page-width"><section className="explore-heading"><div><p>449 job-covered Census places</p><h1>Explore beyond your first five.</h1><span>Major job centers appear first. Search or filter to reveal more places without hiding coverage gaps.</span></div><div className="search-controls"><label><Search size={18}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search city or state"/></label><select aria-label="Filter by state" value={state} onChange={e=>setState(e.target.value)}><option value="ALL">All states + DC</option>{states.map(value=><option key={value}>{value}</option>)}</select></div></section><GeoPlot cities={visible} onOpen={onOpen}/><div className="explore-list">{visible.map(city=>{const p=profileMap.get(city.slug);return <button key={city.place_geoid} onClick={()=>onOpen(city)}><span><strong>{city.name}, {city.state_code}</strong><small>{confidence(city,p)} · Updated {city.latest_listing_date}</small></span><span className="role-count">{city.active_listing_count}<small>roles</small></span><ChevronRight size={19}/></button>})}</div></main>;
}

function DetailScreen({ city, detail, jobs, loading, onBack, saved, onSave, onTradeoffs }: { city:ExploreCity; detail:CityDetail|null; jobs:JobListing[]; loading:boolean; onBack:()=>void; saved:boolean; onSave:()=>void; onTradeoffs:()=>void }) {
  return <main className="detail-page page-width"><button className="back-link" onClick={onBack}><ArrowLeft size={18}/> Back to explore</button><section className="detail-hero"><div><p>{city.state_code} · {city.active_listing_count} covered roles</p><h1>{city.name}</h1><span>{detail?.summary.headline ?? "Job coverage is available; complete city evidence is still expanding."}</span></div><div className="detail-actions"><button className="primary-button" onClick={onSave}><Heart size={18} fill={saved?"currentColor":"none"}/>{saved?"Saved":"Save city"}</button><button className="secondary-button" onClick={onTradeoffs}><SlidersHorizontal size={18}/>Test tradeoffs</button></div></section><section className="metric-strip">{detail ? <><div><small>WSIS score</small><strong>{detail.summary.overall_score.toFixed(1)}</strong></div><div><small>Median rent</small><strong>{money(detail.metrics.median_rent)}</strong></div><div><small>Median income</small><strong>{money(detail.metrics.median_income)}</strong></div><div><small>Commute</small><strong>{detail.metrics.mean_commute_minutes.toFixed(0)} min</strong></div></> : <><div><small>Active roles</small><strong>{city.active_listing_count}</strong></div><div><small>Evidence</small><strong>Expanding</strong></div><div><small>Source date</small><strong>{city.latest_listing_date}</strong></div></>}</section>{detail ? <section className="evidence-section"><div><p>Decision evidence</p><h2>What the current data says</h2></div><ul>{detail.highlights.map(item=><li key={item}><Check size={18}/>{item}</li>)}</ul></section>:null}<section className="jobs-section"><div className="section-title"><div><p>Live opportunity context</p><h2>Roles connected to {city.name}</h2></div><span>{Math.min(jobs.length,20)} shown · partial feed</span></div>{loading?<LoadingCards/>:<div className="job-list">{jobs.slice(0,20).map(job=><a key={`${job.job_id}-${job.place_geoid}`} href={job.job_url} target="_blank" rel="noreferrer"><span><strong>{job.title}</strong><small>{job.company_name} · {job.locations}</small></span><span><small>{job.category}</small><ArrowRight size={18}/></span></a>)}</div>}</section>{detail?.reddit_panel ? <aside className="resident-panel"><p>What some residents report</p><h2>Context only—not part of the score</h2><span>{detail.reddit_panel.summary}</span><small>{detail.reddit_panel.posts_analyzed} posts in the current precomputed sample · {detail.reddit_panel.generated_at}</small></aside>:null}</main>;
}

function TradeoffsScreen({ profile, onChange, cities, onOpen }: { profile:UserProfile; onChange:(p:UserProfile)=>void; cities:ExploreCity[]; onOpen:(c:ExploreCity)=>void }) {
  const alternatives=[{label:"Strongest job depth",city:cities[0]},{label:"Similar but less crowded",city:cities[4]},{label:"More affordable target",city:cities[8]},{label:"Transparent wildcard",city:cities[12]}].filter(item=>item.city);
  return <main className="content-page page-width"><section className="tradeoff-heading"><p>Tradeoff lab</p><h1>Change one assumption. See what opens up.</h1><span>Hard constraints remain hard. This preview never lets a lifestyle preference rescue an unaffordable move.</span></section><div className="tradeoff-layout"><section className="control-panel"><label><span>Safe monthly housing payment</span><div className="range-line"><input type="range" min="700" max="5000" step="100" value={profile.housingBudget} onChange={e=>onChange({...profile,housingBudget:Number(e.target.value)})}/><output>{money(profile.housingBudget)}</output></div></label><label><span>Place scale</span><select value={profile.placeScale} onChange={e=>onChange({...profile,placeScale:e.target.value as UserProfile["placeScale"]})}><option value="major">Major city</option><option value="midsize">Mid-sized city</option><option value="small">Small place</option><option value="open">Open to any</option></select></label><label><span>Green access</span><select value={profile.greenery} onChange={e=>onChange({...profile,greenery:e.target.value as UserProfile["greenery"]})}><option value="parks">Everyday parks</option><option value="nature">Weekend nature</option><option value="both">Both</option><option value="open">No preference</option></select></label></section><section className="alternative-list">{alternatives.map(item=><button key={item.label} onClick={()=>onOpen(item.city)}><span className="round-icon"><Compass size={22}/></span><span><strong>{item.label}</strong><small>{item.city.name}, {item.city.state_code} · {item.city.active_listing_count} roles</small></span><ChevronRight size={20}/></button>)}</section></div></main>;
}

function SavedScreen({ savedCities, onOpen }: { savedCities:ExploreCity[]; onOpen:(c:ExploreCity)=>void }) { return <main className="content-page page-width"><section className="saved-heading"><p>Your action plan</p><h1>Saved places and follow-ups.</h1><span>Sign in will sync these later. For now, they stay only in this browser.</span></section>{savedCities.length?<div className="saved-grid">{savedCities.map(city=><button key={city.place_geoid} onClick={()=>onOpen(city)}><MapPin size={20}/><span><strong>{city.name}, {city.state_code}</strong><small>{city.active_listing_count} active roles</small></span><ChevronRight size={19}/></button>)}</div>:<div className="empty-state"><Heart size={32}/><h2>No saved places yet</h2><p>Save a match or city to build a shortlist and follow its jobs and affordability changes.</p></div>}<section className="action-list"><button><Bell size={21}/><span><strong>Daily matching-job digest</strong><small>Requires verified email and explicit opt-in.</small></span></button><button><CircleDollarSign size={21}/><span><strong>Weekly affordability digest</strong><small>Only meaningful changes; no noisy repeats.</small></span></button><button><MapPin size={21}/><span><strong>Plan a scouting visit</strong><small>Neighborhoods, commute checks, and facts to verify locally.</small></span></button></section></main>; }

export function App() {
  const [view,setView]=useState<View>("intent"); const [previousView,setPreviousView]=useState<View>("explore");
  const [profile,setProfile]=useState<UserProfile>(EMPTY_PROFILE); const [cities,setCities]=useState<ExploreCity[]>([]); const [profiles,setProfiles]=useState<CitySummary[]>([]);
  const [selected,setSelected]=useState<ExploreCity|null>(null); const [detail,setDetail]=useState<CityDetail|null>(null); const [jobs,setJobs]=useState<JobListing[]>([]); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
  const [saved,setSaved]=useState<Set<string>>(()=>new Set(JSON.parse(localStorage.getItem("wsis:saved")??"[]") as string[]));
  const [authEmail,setAuthEmail]=useState(""); const [authOpen,setAuthOpen]=useState(false);
  const loadData=()=>{setLoading(true);setError("");Promise.all([fetchExplore(449),fetchProfiles()]).then(([places,cityProfiles])=>{setCities(places);setProfiles(cityProfiles)}).catch(err=>setError(err instanceof Error?err.message:"Unable to load data")).finally(()=>setLoading(false));};
  useEffect(loadData,[]);
  useEffect(()=>{let unsubscribe:()=>void=()=>undefined;void currentUser().then(user=>setAuthEmail(user?.email??""));void subscribeToAuth(user=>setAuthEmail(user?.email??"")).then(cleanup=>{unsubscribe=cleanup});return()=>unsubscribe()},[]);
  const selectIntent=(intent:IntentId)=>{setProfile({...EMPTY_PROFILE,intent}); if(intent==="explore")setView("explore");else setView("questions")};
  const openCity=(city:ExploreCity)=>{setPreviousView(view);setSelected(city);setView("detail");setDetail(null);setJobs([]);setLoading(true);const hasProfile=profiles.some(item=>item.slug===city.slug);Promise.all([fetchJobs(city.place_geoid,50),hasProfile?fetchCity(city.slug):Promise.resolve(null)]).then(([cityJobs,cityDetail])=>{setJobs(cityJobs);setDetail(cityDetail)}).catch(err=>setError(err instanceof Error?err.message:"Unable to load city details")).finally(()=>setLoading(false));};
  const toggleSaved=(city:ExploreCity)=>setSaved(current=>{const next=new Set(current);if(next.has(city.place_geoid))next.delete(city.place_geoid);else next.add(city.place_geoid);localStorage.setItem("wsis:saved",JSON.stringify([...next]));return next});
  const savedCities=cities.filter(city=>saved.has(city.place_geoid));
  if(view==="intent")return <IntentScreen onSelect={selectIntent}/>;
  if(view==="questions")return <QuestionsScreen profile={profile} cities={cities} onChange={setProfile} onBack={()=>setView("intent")} onComplete={()=>{if(profile.role.trim()){setLoading(true);fetchExplore(449,profile.role).then(matches=>setCities(matches.length?matches:cities)).catch(err=>setError(err instanceof Error?err.message:"Unable to match roles")).finally(()=>setLoading(false));}setView("results")}}/>;
  return <div className="product-shell"><AppHeader view={view} onNavigate={setView} authEmail={authEmail} onSignIn={()=>setAuthOpen(true)} onSignOut={()=>void signOut().then(()=>setAuthEmail(""))}/>{error?<div className="error-banner"><span>{error}</span><button onClick={loadData}>Retry</button></div>:null}{view==="results"?<ResultsScreen profile={profile} cities={cities} profiles={profiles} onOpen={openCity} onExplore={()=>setView("explore")} saved={saved} toggleSaved={toggleSaved}/>:null}{view==="explore"?<ExploreScreen cities={cities} profiles={profiles} onOpen={openCity}/>:null}{view==="detail"&&selected?<DetailScreen city={selected} detail={detail} jobs={jobs} loading={loading} onBack={()=>setView(previousView)} saved={saved.has(selected.place_geoid)} onSave={()=>toggleSaved(selected)} onTradeoffs={()=>setView("tradeoffs")}/>:null}{view==="tradeoffs"?<TradeoffsScreen profile={profile} onChange={setProfile} cities={cities} onOpen={openCity}/>:null}{view==="saved"?<SavedScreen savedCities={savedCities} onOpen={openCity}/>:null}<MobileNav view={view} onNavigate={setView}/><AuthDialog open={authOpen} onClose={()=>setAuthOpen(false)}/></div>;
}
