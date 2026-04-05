import { create } from 'zustand';

const DEMO_POSTS = [
  { id: '86fb8794-34c5-41e6-a5ce-b1c145874e0f', post_url: 'https://www.instagram.com/p/DWtyUT2E5Tu/', username: 'filmseal', caption: 'Charlie Heaton and Lashana Lynch have officially joined the cast of the upcoming Peaky Blinders sequel series.\n\nSet in the 1950s, around a decade after Peaky Blinders: The Immortal Man, the new chapter is coming soon to Netflix.\n\n#peakyblinders #filmseal', likes_count: '593', comments_count: '18', image_url: 'https://scontent.cdninstagram.com/v/t51.82787-15/658022673_18197306827352463_1579663496595380507_n.jpg?stp=c288.0.864.864a_dst-jpg_e35_s640x640_tt6&_nc_cat=101&ccb=7-5&_nc_sid=18de74&efg=eyJlZmdfdGFnIjoiQ0FST1VTRUxfSVRFTS5iZXN0X2ltYWdlX3VybGdlbi5DMyJ9&_nc_ohc=f47304y2SnIQ7kNvwEFRF6Y&_nc_oc=AdqD6qEP-PepVw6xnwjLqx2pr6U_hsId28vZk355b0KHVfpyIAIVFcHF2NW90gPTWbBsjmPkoCaO2jiilNHsGHdw&_nc_zt=23&_nc_ht=scontent.cdninstagram.com&_nc_gid=RUXP3vQ121jnpCy7mfpndw&_nc_ss=7a3a8&oh=00_Af1aMBquQlnn00wH8XPEr06E7qQzSpr_bGwPVn-xqK-8bw&oe=69D7047C', post_date: '2026-04-04 15:50:55+00', post_date_raw: '15 min', hashtags: ['#peakyblinders', '#filmseal'], post_type: 'image' },
  { id: 'a1b2c3d4-dead-beef-cafe-1234567890ab', post_url: 'https://www.instagram.com/p/DWexample01/', username: 'breakingnews_verify', caption: 'BREAKING: Massive flooding reported in coastal areas. Over 10,000 displaced. Authorities urge immediate evacuation. Share this urgent update!\n\n#flooding #emergency #climatecrisis', likes_count: '4821', comments_count: '312', image_url: null, post_date: '2026-04-03 09:15:00+00', post_date_raw: '1d', hashtags: ['#flooding', '#emergency', '#climatecrisis'], post_type: 'image' },
  { id: 'd4e5f6a7-cafe-dead-b00b-abcdef012345', post_url: 'https://www.instagram.com/p/DWexample02/', username: 'sciencedaily', caption: 'Researchers at MIT have developed a new solar panel technology achieving 47% efficiency — almost double today\'s best commercial panels.\n\n#solar #renewable #science #MIT', likes_count: '11204', comments_count: '891', image_url: null, post_date: '2026-04-02 14:30:00+00', post_date_raw: '2d', hashtags: ['#solar', '#renewable', '#science', '#MIT'], post_type: 'image' },
  { id: 'e5f6a7b8-b00b-cafe-dead-bcdef0123456', post_url: 'https://www.instagram.com/p/DWexample03/', username: 'conspiracy_facts_real', caption: 'They don\'t want you to know this! 5G towers near hospitals are mind-control devices funded by globalist elites. WAKE UP!! Share before deleted!!\n\n#5g #truth #expose', likes_count: '392', comments_count: '1420', image_url: null, post_date: '2026-04-01 20:45:00+00', post_date_raw: '3d', hashtags: ['#5g', '#truth', '#expose'], post_type: 'image' },
];

export const useStore = create((set, get) => ({
  // ── connection state ──
  dbStatus: 'idle',      // idle | loading | connected | error
  dbLabel: 'Not connected',

  // ── data ──
  posts: [],
  verdicts: {},          // postId → { verdict, confidence, synthesis, agents }
  analyzing: {},         // postId → true while running

  // ── UI ──
  activeFilter: 'all',
  selectedPost: null,
  showConfigModal: true,
  showPostModal: false,
  view: 'feed',          // feed | arch

  // ── actions ──
  setView: (view) => set({ view }),
  setFilter: (f) => set({ activeFilter: f }),
  setSelectedPost: (post) => set({ selectedPost: post, showPostModal: !!post }),
  closePostModal: () => set({ showPostModal: false, selectedPost: null }),
  openConfig: () => set({ showConfigModal: true }),
  closeConfig: () => set({ showConfigModal: false }),

  loadDemo: () => {
    set({
      posts: DEMO_POSTS,
      dbStatus: 'connected',
      dbLabel: 'Demo mode — 4 posts loaded',
      showConfigModal: false,
      verdicts: {},
    });
  },

  setPosts: (posts, label) => set({
    posts,
    dbStatus: 'connected',
    dbLabel: label,
    showConfigModal: false,
  }),

  setDbLoading: (label) => set({ dbStatus: 'loading', dbLabel: label }),
  setDbError: (label) => set({ dbStatus: 'error', dbLabel: label }),

  setVerdict: (postId, verdict) =>
    set((s) => ({ verdicts: { ...s.verdicts, [postId]: verdict } })),

  setAnalyzing: (postId, flag) =>
    set((s) => ({ analyzing: { ...s.analyzing, [postId]: flag } })),

  deleteVerdict: (postId) =>
    set((s) => {
      const v = { ...s.verdicts };
      delete v[postId];
      return { verdicts: v };
    }),

  getFilteredPosts: () => {
    const { posts, verdicts, activeFilter } = get();
    if (activeFilter === 'all') return posts;
    if (activeFilter === 'unanalyzed') return posts.filter((p) => !verdicts[p.id]);
    return posts.filter((p) => verdicts[p.id]?.verdict === activeFilter);
  },

  getStats: () => {
    const { posts, verdicts } = get();
    return {
      total: posts.length,
      verified: posts.filter((p) => verdicts[p.id]?.verdict === 'verified').length,
      suspicious: posts.filter((p) => verdicts[p.id]?.verdict === 'suspicious').length,
      fake: posts.filter((p) => verdicts[p.id]?.verdict === 'fake').length,
    };
  },
}));
