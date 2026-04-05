/**
 * InstaGrab – Popup Logic
 * Handles scraping, preview, database saving, and history
 */

(function () {
  'use strict';

  // ─── DOM References ──────────────────────────────────
  const statusBar = document.getElementById('status-bar');
  const notInstagram = document.getElementById('not-instagram');
  const mainContent = document.getElementById('main-content');

  const btnScrape = document.getElementById('btn-scrape');
  const btnSave = document.getElementById('btn-save');
  const btnCopy = document.getElementById('btn-copy');
  const btnDownload = document.getElementById('btn-download');
  const btnToggleJson = document.getElementById('btn-toggle-json');
  const btnToggleHistory = document.getElementById('btn-toggle-history');

  const previewCard = document.getElementById('preview-card');
  const previewUsername = document.getElementById('preview-username');
  const previewDate = document.getElementById('preview-date');
  const previewImage = document.getElementById('preview-image');
  const previewImageContainer = document.getElementById('preview-image-container');
  const previewLikes = document.getElementById('preview-likes');
  const previewComments = document.getElementById('preview-comments');
  const previewHashtags = document.getElementById('preview-hashtags');
  const previewCaption = document.getElementById('preview-caption');

  const jsonOutput = document.getElementById('json-output');
  const exportRow = document.getElementById('export-row');
  const historyList = document.getElementById('history-list');
  const historyCount = document.getElementById('history-count');
  const dbStatus = document.getElementById('db-status');

  // ─── State ──────────────────────────────────────────
  let scrapedData = null;
  let jsonVisible = false;
  let historyVisible = false;

  // ─── Init ──────────────────────────────────────────
  init();

  async function init() {
    // Check if we're on Instagram
    const tab = await getCurrentTab();
    const isInstagram = tab && tab.url && tab.url.includes('instagram.com');

    if (!isInstagram) {
      notInstagram.classList.remove('hidden');
      mainContent.classList.add('hidden');
      return;
    }

    notInstagram.classList.add('hidden');
    mainContent.classList.remove('hidden');

    // Check DB connectivity
    checkDbConnection();

    // Load history
    loadHistory();

    // Bind events
    btnScrape.addEventListener('click', handleScrape);
    btnSave.addEventListener('click', handleSave);
    btnCopy.addEventListener('click', handleCopy);
    btnDownload.addEventListener('click', handleDownload);
    btnToggleJson.addEventListener('click', toggleJson);
    btnToggleHistory.addEventListener('click', toggleHistory);
  }

  // ─── Tab Helper ─────────────────────────────────────
  function getCurrentTab() {
    return new Promise((resolve) => {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        resolve(tabs[0] || null);
      });
    });
  }

  // ─── Status Bar ─────────────────────────────────────
  function showStatus(type, message) {
    statusBar.className = `status-bar ${type}`;
    statusBar.querySelector('.status-text').textContent = message;
    statusBar.classList.remove('hidden');

    if (type !== 'loading') {
      setTimeout(() => {
        statusBar.classList.add('hidden');
      }, 4000);
    }
  }

  function hideStatus() {
    statusBar.classList.add('hidden');
  }

  // ─── Scrape ─────────────────────────────────────────
  async function handleScrape() {
    const tab = await getCurrentTab();
    if (!tab) return;

    // Check if it's a post page (supports /p/, /reel/, /reels/)
    const isPostPage = /instagram\.com\/(p|reels?)\//.test(tab.url);
    if (!isPostPage) {
      showStatus('error', 'Navigate to an Instagram post or reel first');
      return;
    }

    btnScrape.classList.add('loading');
    btnScrape.disabled = true;
    showStatus('loading', 'Scraping post data...');

    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });

      const result = results[0]?.result;

      if (!result || !result.success) {
        showStatus('error', result?.error || 'Failed to scrape post data');
        btnScrape.classList.remove('loading');
        btnScrape.disabled = false;
        return;
      }

      scrapedData = result;
      updatePreview(result);
      showStatus('success', `Scraped @${result.username || 'unknown'} successfully`);
      btnSave.disabled = false;

    } catch (err) {
      console.error('Scrape error:', err);
      showStatus('error', 'Error executing script. Refresh the Instagram page and try again.');
    }

    btnScrape.classList.remove('loading');
    btnScrape.disabled = false;
  }

  // ─── Preview ────────────────────────────────────────
  function updatePreview(data) {
    previewCard.classList.remove('hidden');
    btnToggleJson.classList.remove('hidden');
    exportRow.classList.remove('hidden');

    // Username + post type
    const typeEmoji = data.post_type === 'reel' ? '🎬' : data.post_type === 'carousel' ? '📸' : data.post_type === 'video' ? '🎥' : '📷';
    previewUsername.textContent = data.username ? `${typeEmoji} @${data.username}` : 'Unknown';

    // Date
    if (data.post_date) {
      const d = new Date(data.post_date);
      previewDate.textContent = d.toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      });
    } else {
      previewDate.textContent = data.post_date_raw || 'Unknown date';
    }

    // Image — show first available (image_url, video thumbnail, or first media_url)
    const displayImage = data.image_url || (data.media_urls && data.media_urls[0]) || null;
    if (displayImage) {
      previewImage.src = displayImage;
      previewImage.classList.remove('hidden');
      previewImageContainer.querySelector('.preview-image-placeholder').classList.add('hidden');
    }

    // Stats
    previewLikes.textContent = data.likes_count || '0';
    previewComments.textContent = data.comments_count || '0';
    // Show media count for carousels
    const mediaCount = (data.media_urls && data.media_urls.length > 1) ? `${data.media_urls.length} media` : `${data.hashtags?.length || 0} tags`;
    previewHashtags.textContent = mediaCount;

    // Caption
    const captionEl = previewCaption.querySelector('.caption-text');
    if (data.caption) {
      const highlighted = data.caption.replace(
        /(#[\w\u00C0-\u024F]+)/g,
        '<span style="color: var(--accent-purple); font-weight: 500;">$1</span>'
      );
      captionEl.innerHTML = highlighted;
    } else {
      captionEl.textContent = 'No caption found.';
    }

    // JSON
    jsonOutput.innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));
  }

  // ─── JSON Display ──────────────────────────────────
  function syntaxHighlight(json) {
    return json.replace(
      /("(\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
      (match) => {
        let cls = 'json-number';
        if (/^"/.test(match)) {
          cls = /:$/.test(match) ? 'json-key' : 'json-string';
        } else if (/true|false/.test(match)) {
          cls = 'json-bool';
        } else if (/null/.test(match)) {
          cls = 'json-null';
        }
        return `<span class="${cls}">${match}</span>`;
      }
    );
  }

  function toggleJson() {
    jsonVisible = !jsonVisible;
    jsonOutput.classList.toggle('hidden', !jsonVisible);
    btnToggleJson.querySelector('svg + *') ||
      (btnToggleJson.lastChild.textContent = jsonVisible ? 'Hide Raw JSON' : 'View Raw JSON');
    // Update button text
    const textNode = Array.from(btnToggleJson.childNodes).find(n => n.nodeType === 3);
    if (textNode) textNode.textContent = jsonVisible ? ' Hide Raw JSON' : ' View Raw JSON';
  }

  // ─── Save to DB ────────────────────────────────────
  async function handleSave() {
    if (!scrapedData) return;

    btnSave.classList.add('loading');
    btnSave.disabled = true;
    showStatus('loading', 'Saving to Supabase...');

    try {
      // Prepare post data (without comments and debug info)
      const { comments, success, error, _debug, ...postData } = scrapedData;

      // Upsert the post (on conflict of post_url)
      const savedPosts = await SupabaseClient.upsert('instagram_posts', postData);
      const savedPost = savedPosts[0];

      // Insert comments if any
      let commentsSaved = 0;
      if (comments && comments.length > 0 && savedPost?.id) {
        try {
          // Delete existing comments for this post first (prevents duplicates)
          await SupabaseClient.delete('instagram_comments', `post_id=eq.${savedPost.id}`);

          const commentsWithPostId = comments.map(c => ({
            ...c,
            post_id: savedPost.id
          }));

          // Insert comments in batch
          const saved = await SupabaseClient.insert('instagram_comments', commentsWithPostId);
          commentsSaved = saved.length || comments.length;
        } catch (commentErr) {
          console.warn('Comment save issue:', commentErr.message);
        }
      }

      showStatus('success', `Saved to database! (${commentsSaved} comments)`);

      // Save to local history
      addToHistory(savedPost);

      // Update button state
      btnSave.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <polyline points="20,6 9,17 4,12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Saved ✓
      `;

      setTimeout(() => {
        btnSave.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" stroke="currentColor" stroke-width="2"/>
            <polyline points="17,21 17,13 7,13 7,21" stroke="currentColor" stroke-width="2"/>
            <polyline points="7,3 7,8 15,8" stroke="currentColor" stroke-width="2"/>
          </svg>
          Save to DB
        `;
        btnSave.disabled = false;
      }, 2500);

    } catch (err) {
      console.error('Save error:', err);
      showStatus('error', `Save failed: ${err.message}`);
      btnSave.disabled = false;
    }

    btnSave.classList.remove('loading');
  }

  // ─── Copy / Download ────────────────────────────────
  function handleCopy() {
    if (!scrapedData) return;
    navigator.clipboard.writeText(JSON.stringify(scrapedData, null, 2)).then(() => {
      const originalHTML = btnCopy.innerHTML;
      btnCopy.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <polyline points="20,6 9,17 4,12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
        Copied!
      `;
      setTimeout(() => { btnCopy.innerHTML = originalHTML; }, 1500);
    });
  }

  function handleDownload() {
    if (!scrapedData) return;
    const blob = new Blob([JSON.stringify(scrapedData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `instagrab_${scrapedData.username || 'post'}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ─── History ────────────────────────────────────────
  async function addToHistory(post) {
    const history = await getHistory();
    history.unshift({
      username: post.username,
      post_url: post.post_url,
      saved_at: new Date().toISOString(),
      id: post.id
    });
    // Keep last 20
    if (history.length > 20) history.length = 20;
    chrome.storage.local.set({ instagrab_history: history });
    renderHistory(history);
  }

  function getHistory() {
    return new Promise((resolve) => {
      chrome.storage.local.get('instagrab_history', (result) => {
        resolve(result.instagrab_history || []);
      });
    });
  }

  async function loadHistory() {
    const history = await getHistory();
    renderHistory(history);
  }

  function renderHistory(history) {
    historyCount.textContent = history.length;

    if (history.length === 0) {
      historyList.innerHTML = '<div class="state-panel" style="padding:16px"><p style="font-size:0.72rem">No saved posts yet.</p></div>';
      return;
    }

    historyList.innerHTML = history.map(item => {
      const initial = (item.username || '?')[0];
      const time = new Date(item.saved_at);
      const timeStr = time.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        + ' ' + time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

      return `
        <div class="history-item">
          <div class="history-item-avatar">${initial}</div>
          <div class="history-item-info">
            <span class="history-item-username">@${item.username || 'unknown'}</span>
            <span class="history-item-time">${timeStr}</span>
          </div>
          <span class="history-item-badge">Saved</span>
        </div>
      `;
    }).join('');
  }

  function toggleHistory() {
    historyVisible = !historyVisible;
    historyList.classList.toggle('hidden', !historyVisible);
  }

  // ─── DB Connection Check ────────────────────────────
  async function checkDbConnection() {
    try {
      await SupabaseClient.select('instagram_posts', 'select=id&limit=1');
      dbStatus.classList.remove('error');
    } catch (err) {
      dbStatus.classList.add('error');
      dbStatus.querySelector('.db-dot').nextElementSibling &&
        (dbStatus.lastChild.textContent = ' Disconnected');
    }
  }

})();
