/**
 * InstaGrab Content Script v6
 * Precision scraping with DOM zone isolation.
 * 
 * Instagram's article contains: header → media → engagement → caption → comments
 * Each zone is isolated to prevent cross-contamination of data.
 */

(() => {
  'use strict';

  function getArticle() {
    return document.querySelector('article[role="presentation"]')
        || document.querySelector('article');
  }

  function detectPageType() {
    const url = window.location.href;
    if (/\/reels?\//.test(url)) return 'reel';
    if (/\/p\//.test(url)) return 'post';
    return 'unknown';
  }

  function isProfilePicUrl(url) {
    if (!url) return false;
    if (/\/t51\.2885-19\//.test(url)) return true;
    if (/\/t51\.82787-19\//.test(url)) return true;
    if (/s150x150/.test(url)) return true;
    if (/s44x44/.test(url)) return true;
    if (/s32x32/.test(url)) return true;
    if (/s64x64/.test(url)) return true;
    if (/giphy\.com|external\./.test(url)) return true;
    return false;
  }

  function isPostImageUrl(url) {
    if (!url) return false;
    if (/\/t51\.\d+-15\//.test(url)) return true;
    if (/\/t39\.\d+-6\//.test(url)) return true;
    return false;
  }

  // ─── Username ───────────────────────────────────────

  const NAV_NAMES = new Set([
    'explore','reels','reel','direct','accounts','about','stories',
    'p','home','search','create','notifications','messages','profile',
    'settings','nametag','session','challenge','404','privacy',
    'legal','terms','emails','directory'
  ]);

  function extractUsernameFromHref(href) {
    if (!href) return null;
    let m = href.match(/instagram\.com\/([A-Za-z0-9._]+)\/?(?:\?.*)?$/);
    if (m && !NAV_NAMES.has(m[1].toLowerCase())) return m[1];
    m = href.match(/^\/([A-Za-z0-9._]+)\/?$/);
    if (m && !NAV_NAMES.has(m[1].toLowerCase())) return m[1];
    return null;
  }

  function scrapeUsername() {
    const article = getArticle();
    if (article) {
      const header = article.querySelector('header');
      if (header) {
        const links = header.querySelectorAll('a[href]');
        for (const link of links) {
          const name = extractUsernameFromHref(link.getAttribute('href'));
          if (name) return name;
        }
      }
    }

    const allLinks = document.querySelectorAll('a[href]');
    for (const link of allLinks) {
      const name = extractUsernameFromHref(link.getAttribute('href'));
      if (!name) continue;
      const text = link.textContent.trim();
      if (text.length < 1 || text.length > 50) continue;
      const parent = link.parentElement;
      if (parent && /Follow|Suivre|Seguir|Folgen/i.test(parent.textContent || '')) return name;
      if (text === name && text.length > 1 && text.length < 31) return name;
    }

    const urlMatch = window.location.pathname.match(/^\/([A-Za-z0-9._]+)\/(?:p|reels?)\//);
    if (urlMatch && !NAV_NAMES.has(urlMatch[1].toLowerCase())) return urlMatch[1];

    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) {
      const c = ogTitle.getAttribute('content') || '';
      let m = c.match(/@([A-Za-z0-9._]+)/);
      if (m) return m[1];
      m = c.match(/^([A-Za-z0-9._]+)\s+on\s+Instagram/i);
      if (m) return m[1];
    }

    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) {
      const c = ogDesc.getAttribute('content') || '';
      const m = c.match(/[-\u2013\u2014]\s*([A-Za-z0-9._]+)\s+(?:on|sur|en)\s+Instagram/i);
      if (m) return m[1];
    }

    for (const link of allLinks) {
      const name = extractUsernameFromHref(link.getAttribute('href'));
      if (name && name.length > 1 && name.length < 31) return name;
    }

    return null;
  }

  // ─── Caption ────────────────────────────────────────

  function scrapeCaption() {
    const article = getArticle();
    if (article) {
      const h1 = article.querySelector('h1');
      if (h1) {
        const text = h1.textContent.trim();
        if (text.length > 2 && text.toLowerCase() !== 'instagram') return text;
      }
    }

    if (article) {
      const username = scrapeUsername();
      const allLinks = article.querySelectorAll('a[href]');
      for (const link of allLinks) {
        const href = link.getAttribute('href') || '';
        if (href === `/${username}/` || href === `/${username}`) {
          if (link.closest('header')) continue;
          const container = link.closest('li') || link.closest('div');
          if (container) {
            const spans = container.querySelectorAll('span');
            for (const span of spans) {
              const text = span.textContent.trim();
              if (text === username) continue;
              if (text.length < 5) continue;
              if (text.toLowerCase() === 'instagram') continue;
              if (/^\d+\s?(h|m|d|w|s|min|sec|j|sem)\b/i.test(text)) continue;
              if (/^(Follow|Suivre|Seguir|Verified|more|plus)$/i.test(text)) continue;
              return text;
            }
          }
        }
      }
    }

    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) {
      let content = ogDesc.getAttribute('content') || '';
      content = content.replace(/^[\d,.\s\u00a0KkMm]+(?:Likes?|J[\u2019']aime|Me gusta)[,\s]*[\d,.\s\u00a0KkMm]*(?:Comments?|commentaires?|comentarios?)\s*[-\u2013\u2014]\s*/i, '');
      content = content.replace(/^[^:]+:\s*"?/, '');
      content = content.replace(/"$/, '');
      if (content.length > 5) return content;
    }

    return null;
  }

  // ─── Likes ──────────────────────────────────────────

  function scrapeLikes() {
    const article = getArticle();
    const likePatterns = [
      /([\d\s,.\u00a0]+[KkMm]?)\s*(?:likes?)\b/i,
      /([\d\s,.\u00a0]+[KkMm]?)\s*(?:j[\u2019\u0027]aime)/i,
      /([\d\s,.\u00a0]+[KkMm]?)\s*(?:mentions?\s*j[\u2019\u0027]aime)/i,
      /([\d\s,.\u00a0]+[KkMm]?)\s*(?:me gusta)/i,
    ];

    if (article) {
      const sections = article.querySelectorAll('section');
      for (const section of sections) {
        if (section.closest('li') || section.closest('ul')) continue;
        const sectionText = section.textContent;
        for (const pattern of likePatterns) {
          const match = sectionText.match(pattern);
          if (match) return match[1].trim();
        }
      }

      const directChildren = article.children;
      for (const child of directChildren) {
        if (child.tagName === 'UL' || child.tagName === 'LI') continue;
        const spans = child.querySelectorAll('span, a, button');
        for (const el of spans) {
          if (el.closest('ul') || el.closest('li')) continue;
          const text = el.textContent.trim();
          for (const pattern of likePatterns) {
            const match = text.match(pattern);
            if (match) return match[1].trim();
          }
        }
      }
    }

    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) {
      const content = ogDesc.getAttribute('content') || '';
      for (const pattern of likePatterns) {
        const match = content.match(pattern);
        if (match) return match[1].trim();
      }
      const numMatch = content.match(/^([\d,.\s\u00a0]+[KkMm]?)\s/);
      if (numMatch) return numMatch[1].trim();
    }

    return null;
  }

  // ─── Comments Count ─────────────────────────────────

  function scrapeCommentsCount() {
    const article = getArticle();
    const patterns = [
      /(?:View|See)\s+all\s+([\d,]+)\s+comment/i,
      /Voir\s+les?\s+([\d\s,]+)\s+commentaire/i,
      /Ver\s+los?\s+([\d,]+)\s+comentario/i,
    ];

    if (article) {
      const elements = article.querySelectorAll('a, span, button, div[role="button"]');
      for (const el of elements) {
        const text = el.textContent.trim();
        for (const pattern of patterns) {
          const match = text.match(pattern);
          if (match) return match[1].replace(/\s/g, '');
        }
      }
    }

    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) {
      const content = ogDesc.getAttribute('content') || '';
      const m = content.match(/(\d[\d,.\s]*[KkMm]?)\s*(?:Comments?|commentaires?|comentarios?)/i);
      if (m) {
        let num = m[1].trim();
        num = num.replace(/^[,.\s]+/, '').replace(/[,.\s]+$/, '');
        return num;
      }
    }

    return null;
  }

  // ─── Post Images ────────────────────────────────────

  function scrapeAllImages() {
    const article = getArticle();
    if (!article) {
      const ogImage = document.querySelector('meta[property="og:image"]');
      return {
        main: ogImage ? ogImage.getAttribute('content') : null,
        all: ogImage ? [ogImage.getAttribute('content')] : []
      };
    }

    const postImages = [];
    const allImgs = article.querySelectorAll('img[src]');
    for (const img of allImgs) {
      const src = img.getAttribute('src') || '';
      if (!src || src.startsWith('data:')) continue;
      if (isProfilePicUrl(src)) continue;
      const parentLi = img.closest('li');
      if (parentLi) {
        const profileLink = parentLi.querySelector('a[href]');
        if (profileLink && /^\/[A-Za-z0-9._]+\/?$/.test(profileLink.getAttribute('href') || '')) continue;
      }
      if (img.closest('header')) continue;
      if (isPostImageUrl(src)) {
        let bestUrl = src;
        const srcset = img.getAttribute('srcset') || '';
        if (srcset) {
          const parts = srcset.split(',').map(s => s.trim());
          let maxW = 0;
          for (const part of parts) {
            const tokens = part.split(/\s+/);
            if (tokens.length >= 2) {
              const dw = parseInt(tokens[1]) || 0;
              if (dw > maxW) { maxW = dw; bestUrl = tokens[0]; }
            }
          }
        }
        if (!postImages.includes(bestUrl)) postImages.push(bestUrl);
      }
    }

    if (postImages.length === 0) {
      const ogImage = document.querySelector('meta[property="og:image"]');
      if (ogImage) {
        const ogSrc = ogImage.getAttribute('content');
        if (ogSrc) postImages.push(ogSrc);
      }
    }

    return { main: postImages[0] || null, all: postImages };
  }

  // ─── Video ──────────────────────────────────────────

  function scrapeVideo() {
    const videos = document.querySelectorAll('video');
    for (const video of videos) {
      const src = video.getAttribute('src') || '';
      const poster = video.getAttribute('poster') || null;
      const source = video.querySelector('source[src]');
      const sourceSrc = source ? source.getAttribute('src') : null;
      const videoUrl = (src && !src.startsWith('blob:')) ? src : sourceSrc;
      if (videoUrl || poster) return { url: videoUrl || null, poster };
    }
    const ogVideo = document.querySelector('meta[property="og:video"]');
    if (ogVideo) return { url: ogVideo.getAttribute('content'), poster: null };
    return { url: null, poster: null };
  }

  // ─── Date ───────────────────────────────────────────

  function scrapeDate() {
    const article = getArticle();
    const searchRoot = article || document;
    const timeEl = searchRoot.querySelector('time[datetime]');
    if (timeEl) {
      return { iso: timeEl.getAttribute('datetime'), display: timeEl.textContent.trim() || timeEl.getAttribute('title') };
    }
    return { iso: null, display: null };
  }

  // ─── Hashtags ───────────────────────────────────────

  function scrapeHashtags(caption) {
    if (!caption) return [];
    const matches = caption.match(/#[\w\u00C0-\u024F\u0600-\u06FF]+/g);
    return matches ? [...new Set(matches)] : [];
  }

  // ─── Comments ───────────────────────────────────────

  function isUiText(text) {
    if (!text || text.length < 1) return true;
    if (/^\d+\s?(h|m|d|w|s|j|sem|min|sec|hr|heure|jour|semaine)\b/i.test(text)) return true;
    if (/^(Reply|Répondre|Responder|Antworten)$/i.test(text)) return true;
    if (/^(Like|J[\u2019']aime|Me gusta|Gefällt)$/i.test(text)) return true;
    if (/^(Follow|Suivre|Seguir|Folgen|Verified|Suivi\(e\))$/i.test(text)) return true;
    if (/^(more|plus|más|mehr|\.{3})$/i.test(text)) return true;
    if (/^(View|Voir|Ver|See)\s/i.test(text) && text.length < 50) return true;
    if (/^\d+\s*(likes?|j[\u2019']aime|réponses?|replies?|respuestas?)/i.test(text)) return true;
    if (/^(Home|Search|Explore|Reels|Messages|Notifications|Create|Profile|More|Accueil|Rechercher|Explorer|Instagram)$/i.test(text)) return true;
    if (/^(Ajouter|Add)\s/i.test(text) && text.length < 40) return true;
    if (/^(il y a|ago)\b/i.test(text)) return true;
    return false;
  }

  function scrapeComments(maxComments = 10) {
    const article = getArticle();
    if (!article) return [];

    const postAuthor = scrapeUsername();
    const comments = [];
    const seen = new Set();
    let captionSkipped = false;

    // ━━━ APPROACH: Walk every <a> in the ENTIRE article ━━━
    // For each profile link found, walk UP to find a comment-like container.
    // Then extract text spans from that container.

    const everyLink = article.getElementsByTagName('a');

    for (let i = 0; i < everyLink.length; i++) {
      if (comments.length >= maxComments) break;

      const link = everyLink[i];
      const href = link.getAttribute('href') || '';

      // Extract username from href
      const commenter = extractUsernameFromHref(href);
      if (!commenter) continue;

      // Skip header links
      if (link.closest('header')) continue;

      // Skip post author's caption (first occurrence)
      if (commenter === postAuthor && !captionSkipped) {
        captionSkipped = true;
        continue;
      }

      // Skip duplicate usernames we've already processed from same container
      // Walk up to find the container: try li first, then walk up divs
      let container = null;

      // Try closest li
      container = link.closest('li');

      // If no li, walk up and find a reasonable container (div with a time element)
      if (!container) {
        let el = link.parentElement;
        for (let depth = 0; depth < 8 && el && el !== article; depth++) {
          // A good comment container has a time element and some spans
          if (el.querySelector('time') || el.querySelectorAll('span').length >= 2) {
            container = el;
            break;
          }
          el = el.parentElement;
        }
      }

      if (!container || container === article) continue;

      // Extract comment text: find longest non-UI span
      let commentText = '';
      const spans = container.querySelectorAll('span');

      for (const span of spans) {
        // Don't go into nested containers that are different comments
        if (container.tagName === 'LI') {
          const spanLi = span.closest('li');
          if (spanLi && spanLi !== container) continue;
        }

        const text = span.textContent.trim();
        if (text === commenter) continue;
        if (text === postAuthor) continue;
        if (isUiText(text)) continue;

        if (text.length > commentText.length) {
          commentText = text;
        }
      }

      // Accept emoji-only comments (≥1 char)
      if (!commentText) {
        for (const span of spans) {
          const text = span.textContent.trim();
          if (text === commenter || text === postAuthor) continue;
          if (text.length >= 1 && !/^\d+\s?(h|m|d|w|s|j)\b/i.test(text) &&
              !/^(Reply|Répondre|Like|Follow|Suivre|Verified)$/i.test(text)) {
            commentText = text;
            break;
          }
        }
      }

      if (!commentText) continue;

      // Dedup
      const key = `${commenter}:${commentText.substring(0, 40)}`;
      if (seen.has(key)) continue;
      seen.add(key);

      const timeEl = container.querySelector('time[datetime]');
      comments.push({
        commenter_username: commenter,
        comment_text: commentText,
        comment_date: timeEl ? timeEl.getAttribute('datetime') : null
      });
    }

    return comments;
  }

  // ─── Main ──────────────────────────────────────────

  function scrapePost() {
    const url = window.location.href;
    if (!/instagram\.com\/(?:p|reels?)\//.test(url)) {
      return { success: false, error: 'Navigate to an Instagram post or reel first.' };
    }

    const pageType = detectPageType();
    const caption = scrapeCaption();
    const dateInfo = scrapeDate();
    const comments = scrapeComments();
    const imageData = scrapeAllImages();
    const videoData = scrapeVideo();

    let postType = pageType === 'reel' ? 'reel' : 'image';
    if (pageType === 'post' && imageData.all.length > 1) postType = 'carousel';
    if (pageType === 'post' && videoData.url) postType = 'video';

    let mainImage = imageData.main;
    if (!mainImage && videoData.poster) mainImage = videoData.poster;

    const mediaUrls = [...imageData.all];
    if (videoData.url && !mediaUrls.includes(videoData.url)) mediaUrls.push(videoData.url);
    if (videoData.poster && !mediaUrls.includes(videoData.poster) && !isProfilePicUrl(videoData.poster)) {
      mediaUrls.push(videoData.poster);
    }

    // Debug: collect raw data about what's in the DOM
    const article = getArticle();
    const debugHrefs = [];
    if (article) {
      const links = article.getElementsByTagName('a');
      for (let i = 0; i < Math.min(links.length, 20); i++) {
        debugHrefs.push(links[i].getAttribute('href'));
      }
    }
    const _debug = {
      has_article: !!article,
      time_count: article ? article.querySelectorAll('time[datetime]').length : 0,
      link_count: article ? article.getElementsByTagName('a').length : 0,
      li_count: article ? article.querySelectorAll('li').length : 0,
      span_count: article ? article.querySelectorAll('span').length : 0,
      first_20_hrefs: debugHrefs,
      comments_found: comments.length,
    };

    return {
      success: true,
      post_url: url.split('?')[0],
      username: scrapeUsername() || 'unknown',
      caption: caption,
      likes_count: scrapeLikes(),
      comments_count: scrapeCommentsCount(),
      image_url: mainImage,
      video_url: videoData.url,
      media_urls: mediaUrls,
      post_type: postType,
      post_date: dateInfo.iso,
      post_date_raw: dateInfo.display,
      hashtags: scrapeHashtags(caption),
      comments: comments,
      scraped_at: new Date().toISOString(),
      _debug: _debug
    };
  }

  return scrapePost();
})();
