<script lang="ts">
  import { onMount } from 'svelte';
  import DraggableSticker from '$lib/components/DraggableSticker.svelte';

  // --- Types ---
  type Sticker = {
    id: string;
    src: string;
    x: number;
    y: number;
    rotation: number;
    scale: number;
    on_back: boolean;
  };

  type Polaroid = {
    id: string;
    src: string;
    createdAt: Date;
    description: string;
    diaryEntry: string;
    stickers: Sticker[];
    editing: boolean;
    showBack: boolean;
  };

  const API_URL = 'http://localhost:9999';
  let polaroids: Polaroid[] = [];
  let polaroidElements: { [id: string]: HTMLElement } = {};

  // --- Fetch ---
  onMount(async () => {
    try {
      const response = await fetch(`${API_URL}/polaroids`);
      if (!response.ok) throw new Error('Failed to fetch polaroids');

      const data = await response.json();
      polaroids = data.map((p: any) => ({
        ...p,
        src: p.src,
        createdAt: new Date(p.createdAt),
        editing: false,
        showBack: false,
        diaryEntry: p.diary_entry || "",
        stickers: p.stickers?.map((s: any) => ({
          ...s,
          src: s.src,
        })) || []
      }));
    } catch (error) {
      console.error('Error fetching polaroids:', error);
    }
  });

  // --- File Upload ---
  async function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files[0]) {
      const file = target.files[0];
      const reader = new FileReader();

      reader.onload = async (e) => {
        if (typeof e.target?.result === 'string') {
          try {
            const response = await fetch(`${API_URL}/polaroids`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ image_base64: e.target.result })
            });
            if (!response.ok) throw new Error('Failed to upload polaroid');

            const data = await response.json();
            const newPolaroid: Polaroid = {
              ...data,
              src: data.src,
              createdAt: new Date(data.createdAt),
              editing: true,
              showBack: false,
              diaryEntry: data.diary_entry || "",
              stickers: data.stickers?.map((s: any) => ({ ...s, src: s.src })) || []
            };
            polaroids = [...polaroids, newPolaroid];
          } catch (error) {
            console.error('Upload error:', error);
          }
        }
      };
      reader.readAsDataURL(file);
    }
  }

  // --- Edit & Save ---
  function toggleEdit(id: string) {
    polaroids = polaroids.map((p) => p.id === id ? { ...p, editing: !p.editing } : p);
  }

  async function saveChanges(polaroid: Polaroid) {
    try {
      const response = await fetch(`${API_URL}/polaroids/${polaroid.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: polaroid.description,
          diary_entry: polaroid.diaryEntry,
          createdAt: polaroid.createdAt.toISOString(),
          stickers: polaroid.stickers
        })
      });

      if (!response.ok) throw new Error('Failed to save polaroid');
    } catch (err) {
      console.error('Save error:', err);
    }
  }

  async function handleSaveAndExit(polaroid: Polaroid) {
    await saveChanges(polaroid);
    toggleEdit(polaroid.id);
  }

  // --- Delete ---
  async function deletePolaroid(id: string) {
    if (!confirm('Delete this polaroid?')) return;
    await fetch(`${API_URL}/polaroids/${id}`, { method: 'DELETE' });
    polaroids = polaroids.filter((p) => p.id !== id);
  }

  // --- Sticker Updates ---
  function handleStickerUpdate(event: CustomEvent, polaroidId: string) {
    const { id: stickerId, x, y } = event.detail;
    polaroids = polaroids.map((p) =>
      p.id === polaroidId
        ? { ...p, stickers: p.stickers.map((s) => s.id === stickerId ? { ...s, x, y } : s) }
        : p
    );
  }

  function handleStickerToggleSide(stickerId: string, polaroidId: string) {
    polaroids = polaroids.map((p) => {
      if (p.id !== polaroidId) return p;
      const newStickers = p.stickers.map((s) =>
        s.id === stickerId ? { ...s, on_back: !s.on_back } : s
      );
      return { ...p, stickers: newStickers };
    });
  }

  function toggleSide(polaroid: Polaroid) {
    polaroids = polaroids.map((p) =>
      p.id === polaroid.id ? { ...p, showBack: !p.showBack } : p
    );
  }

  function formatDateForInput(date: Date) {
    return new Date(date).toISOString().split('T')[0];
  }

  function handleDateChange(event: Event, id: string) {
    const target = event.target as HTMLInputElement;
    const newDate = new Date(target.value);
    polaroids = polaroids.map((p) => (p.id === id ? { ...p, createdAt: newDate } : p));
  }
</script>

<div class="p-6 min-h-full">
  <h1 class="text-4xl text-rose-500 font-bold mb-8 text-center">Polaroid Memories</h1>

  <!-- Upload -->
  <div class="mb-8 text-center">
    <label for="file-upload" class="cursor-pointer bg-rose-400 hover:bg-rose-500 text-white font-bold py-2 px-4 rounded-full shadow-lg transition-transform hover:scale-105">
      + Add a Polaroid
    </label>
    <input id="file-upload" type="file" class="hidden" on:change={handleFileUpload} accept="image/*" />
  </div>

  {#if polaroids.length === 0}
    <div class="text-center py-20 text-gray-500">Upload a photo to start 📸</div>
  {/if}

  <!-- Grid -->
	<!-- svelte-ignore a11y_consider_explicit_label -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-4">
    {#each polaroids.sort((a,b)=>b.createdAt-a.createdAt) as polaroid (polaroid.id)}
      <div class="bg-white p-4 shadow-lg rounded relative group"
			bind:this={polaroidElements[polaroid.id]}>
        <!-- Controls -->
        <div class="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 z-99">
          {#if polaroid.editing}
            <button on:click={() => handleSaveAndExit(polaroid)} class="bg-rose-400 text-white rounded-full px-3 py-1 text-sm">Save</button>
          {:else}
            <button on:click={() => toggleEdit(polaroid.id)} class="bg-white p-2 rounded-full shadow">
							<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pencil-icon lucide-pencil"><path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/></svg></button>
            <button on:click={() => deletePolaroid(polaroid.id)} class="bg-white p-2 rounded-full shadow">
							<svg xmlns="http://www.w3.org/2000/svg" width="18" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash2-icon lucide-trash-2"><path d="M10 11v6"/><path d="M14 11v6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
						</button>
          {/if}
          <button on:click={() => toggleSide(polaroid)} class="bg-white p-2 rounded-full shadow"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-refresh-ccw-icon lucide-refresh-ccw"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg></button>
        </div>

        <!-- FRONT -->
        {#if !polaroid.showBack}
          <div class="relative bg-gray-100 border-2 border-gray-200">
            <img src={polaroid.src} alt="Polaroid front" class="w-full h-auto aspect-square object-cover" />
            {#each polaroid.stickers.filter(s => !s.on_back) as sticker (sticker.id)}
              <DraggableSticker
                {sticker}
                editing={polaroid.editing}
                polaroidElement={polaroidElements[polaroid.id]}
                on:update={(e) => handleStickerUpdate(e, polaroid.id)}
                on:dragend={() => saveChanges(polaroid)}
                on:toggleSide={() => handleStickerToggleSide(sticker.id, polaroid.id)}
              />
            {/each}
          </div>
        {:else}
        <!-- BACK -->
          <div class=" bg-rose-100 border-2 border-gray-200 rounded overflow-auto">
            {#if polaroid.editing}
              <textarea
                bind:value={polaroid.diaryEntry}
                placeholder="Write your diary entry..."
                class="p-2 w-full text-sm border rounded bg-white shadow-inner h-[232.5px]"
              ></textarea>
            {:else}
              <p class="bg-gray-100 p-3 text-sm text-gray-700 whitespace-pre-line italic h-[240.5px]">{polaroid.diaryEntry || 'No diary entry yet.'}</p>
            {/if}

            <!-- Stickers on back -->
            {#each polaroid.stickers.filter(s => s.on_back) as sticker (sticker.id)}
              <DraggableSticker
                {sticker}
                editing={polaroid.editing}
                polaroidElement={polaroidElements[polaroid.id]}
                on:update={(e) => handleStickerUpdate(e, polaroid.id)}
                on:dragend={() => saveChanges(polaroid)}
                on:toggleSide={() => handleStickerToggleSide(sticker.id, polaroid.id)}
              />
            {/each}
          </div>
        {/if}

        <!-- Description + Date -->
        <div class="w-full text-center mt-3">
          {#if polaroid.editing}
            <textarea bind:value={polaroid.description} placeholder="Add a description..." class="w-full border p-1 text-sm rounded bg-rose-200"></textarea>
            <input type="date" class="mt-1 w-full border text-xs rounded" value={formatDateForInput(polaroid.createdAt)} on:change={(e)=>handleDateChange(e,polaroid.id)} />
          {:else}
            <p class="italic text-sm text-gray-700">{polaroid.description}</p>
            <div class="text-xs text-gray-500">{polaroid.createdAt.toLocaleDateString()}</div>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>
