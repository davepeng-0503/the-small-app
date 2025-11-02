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
  let loaded = false;
  let loadingCount = 0;
  let skipAiOnUpload = false; // New state for skip AI checkbox
  let regeneratingId: string | null = null; // New state for sticker regeneration loading

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
      loaded=true
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
            loadingCount += 1
            const response = await fetch(`${API_URL}/polaroids`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ 
                image_base64: e.target.result,
                skip_ai: skipAiOnUpload
              })
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
          } finally {
            loadingCount -= 1
          }
        }
      };
      reader.readAsDataURL(file);
    }
  }

  // --- Sticker Regeneration ---
  async function regenerateStickers(polaroidId: string) {
    if (!confirm('This will delete all current stickers and generate new ones. This cannot be undone. Are you sure?')) {
      return;
    }
    regeneratingId = polaroidId;
    try {
      const response = await fetch(`${API_URL}/polaroids/${polaroidId}/stickers`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown server error' }));
        throw new Error(errorData.detail || 'Failed to regenerate stickers');
      }

      const updatedPolaroidData = await response.json();

      polaroids = polaroids.map(p => {
        if (p.id === polaroidId) {
          return {
            ...p, // keep local state like editing, showBack
            description: updatedPolaroidData.description,
            diaryEntry: updatedPolaroidData.diary_entry || "",
            stickers: updatedPolaroidData.stickers?.map((s: any) => ({ ...s, src: s.src })) || [],
          };
        }
        return p;
      });
    } catch (error) {
      console.error('Error regenerating stickers:', error);
      alert(`Could not regenerate stickers: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      regeneratingId = null;
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
  {#if polaroids.length === 0 && loaded}
    <div class="text-center py-20 text-gray-500">Upload a photo to start 📸</div>
  {/if}

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 p-4 mt-10">

    {#if loaded}
      <div class="w-full h-full rounded-2xl bg-white/10 backdrop-blur-lg border border-white/40 shadow-xl flex flex-col justify-between p-2 hover:bg-white/20 transition-all duration-300 hover:scale-105 group">
        <label for="file-upload" class="cursor-pointer flex-grow flex items-center justify-center text-8xl font-thin text-rose-200 group-hover:text-rose-400">
            +
        </label>
        <div class="text-center pb-1">
            <input type="checkbox" id="skip-ai" bind:checked={skipAiOnUpload} class="form-checkbox h-4 w-4 text-rose-400 bg-white/20 border-white/50 rounded focus:ring-rose-500">
            <label for="skip-ai" class="ml-2 text-sm text-white align-middle">Skip AI stickers</label>
        </div>
        <input id="file-upload" type="file" class="hidden" on:change={handleFileUpload} accept="image/*" />
      </div>

      {#if loadingCount > 0}
        <div class="w-full h-full">
          <div class="w-full h-full">
            <div class="
              flex items-center justify-center
              w-full h-full
              rounded-2xl
              
              bg-white/10
              backdrop-blur-lg
              border border-white/40
              shadow-xl
              
              text-md
              font-thin
              text-rose-600
              
              transition-all duration-300
            ">
            Loading {loadingCount} Photos...
            </div>

          </div>
        </div>
      {/if}
    {/if}

    {#each polaroids.sort((a,b)=>b.createdAt-a.createdAt) as polaroid (polaroid.id)}
      <div class="bg-white p-4 shadow-lg rounded relative group hover:scale-105 transition-all"
      bind:this={polaroidElements[polaroid.id]}
      >
        
        <div class="absolute -top-12 right-2 flex gap-2 opacity-0 group-hover:opacity-100 z-99 w-full">
          {#if polaroid.editing}
            <button on:click={() => handleSaveAndExit(polaroid)} class="bg-rose-400 text-white rounded-full px-3 py-1 text-sm">Save</button>
            <button
              on:click={() => regenerateStickers(polaroid.id)}
              class="bg-blue-500 hover:bg-blue-600 text-white rounded-full px-3 py-1 text-sm disabled:opacity-50 disabled:cursor-wait"
              disabled={regeneratingId === polaroid.id}
            >
              {#if regeneratingId === polaroid.id}
                Generating...
              {:else}
                New Stickers
              {/if}
            </button>
          {:else}
            <button on:click={() => toggleEdit(polaroid.id)} class="bg-white p-2 rounded-full shadow">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pencil-icon lucide-pencil"><path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/></svg></button>
            <button on:click={() => deletePolaroid(polaroid.id)} class="bg-white p-2 rounded-full shadow">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash2-icon lucide-trash-2"><path d="M10 11v6"/><path d="M14 11v6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          {/if}
          <button on:click={() => toggleSide(polaroid)} class="bg-white p-2 rounded-full shadow"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-refresh-ccw-icon lucide-refresh-ccw"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg></button>
        </div>

        <div class="relative w-full perspective:1000px">
          
          <div class="invisible"
          >
            <img src={polaroid.src} alt="" class="w-full h-auto aspect-square object-cover" />
          </div>

          <div
            class="absolute top-0 left-0 w-full h-full transition-transform duration-700 ease-in-out transform-style-3d"
            class:rotate-y-180={polaroid.showBack}
          >
            <div class="absolute w-full h-full top-0 left-0 backface-hidden">
              <div class="relative bg-gray-100 border-2 border-gray-200 h-full">
                <img src={polaroid.src} alt="Polaroid front" class="w-full h-full object-cover" />
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
            </div>

            <div class="absolute w-full h-full top-0 left-0 backface-hidden rotate-y-180">
              <div class="bg-gray-100 border-2 border-gray-200 rounded overflow-auto h-full flex flex-col">
                {#if polaroid.editing}
                <textarea
                bind:value={polaroid.diaryEntry}
                placeholder="Add a diary entry..."
                class="p-3 w-full text-gray-700 text-sm rounded whitespace-pre-line italic bg-transparent border-none focus:ring-0 focus:outline-none resize-none"
                style="box-shadow: none; overflow: hidden;"
                rows="1"
                on:input={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = target.scrollHeight + 'px';
                }}
              ></textarea>
                {:else}
                  <p class="bg-gray-100 p-3 text-sm text-gray-700 whitespace-pre-line italic flex-grow min-h-[100px]">{polaroid.diaryEntry || 'No diary entry yet.'}</p>
                {/if}

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
            </div>
          </div>
        </div>
        <div class="w-full text-center mt-3">
          {#if polaroid.editing}
          <textarea
          bind:value={polaroid.description}
          placeholder="Add a description..."
          class="w-full text-center p-0 text-sm rounded bg-transparent border-none focus:ring-0 focus:outline-none resize-none"
          style="box-shadow: none; overflow: hidden;"
          rows="1"
          on:input={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto';
            target.style.height = target.scrollHeight + 'px';
          }}
        ></textarea><input type="date" class="mt-1 w-full border text-xs rounded" value={formatDateForInput(polaroid.createdAt)} on:change={(e)=>handleDateChange(e,polaroid.id)} />
          {:else}
            <p class="italic text-sm text-gray-700">{polaroid.description}</p>
            <div class="text-xs text-gray-500">{polaroid.createdAt.toLocaleDateString()}</div>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>

<style lang="postcss">
  .transform-style-3d {
    transform-style: preserve-3d;
  }
  .backface-hidden {
    backface-visibility: hidden;
  }
  .rotate-y-180 {
    transform: rotateY(180deg);
  }
</style>
