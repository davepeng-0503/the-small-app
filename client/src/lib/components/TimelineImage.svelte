<script lang="ts">
  import type { TimelineItem } from '../../app';
  
  export let item: TimelineItem & { left: boolean }

</script>

<div class="border border-solid bg-white p-3">
  <img
    src={item.src}
    alt={item.id}
  />
</div>