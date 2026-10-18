/* Final.xlsx records grouped into one interactive shape per source unit and year. */
window.createDistrictLayer = function ({ collection, projectPolygons, polygonPath, line, screen, selectRegion, tooltip, fmt }) {
    const max = Math.ceil(collection.metadata.maxPopulation / 100000) * 100000;
    const color = d3.scaleLinear().domain([0, max]).range(['#ffffff', '#f04b2f']).clamp(true);
    const entries = collection.features.map(feature => ({ properties: feature.properties, polygons: projectPolygons(feature.geometry.type === 'MultiPolygon' ? feature.geometry.coordinates : [feature.geometry.coordinates]) }));
    const layer = d3.select('#drawing').insert('g', '#land').attr('id', 'districtFills').attr('clip-path', 'url(#landClip)');
    const available = d3.select('#map defs').append('clipPath').attr('id', 'availableDistrictClip').append('path').attr('fill-rule', 'evenodd');
    let active = false, currentYear = 2025, groups = [];
    function groupRecords(year) {
        const bySource = new Map();
        for (const entry of entries) {
            const record = entry.properties.values[year];
            if (!record) continue; // Missing is removed; a record whose value is zero stays visible.
            const key = record.sourceKey;
            if (!bySource.has(key)) bySource.set(key, { key, record: { ...record }, polygons: [], geometryProvinces: new Set(), parts: [] });
            const group = bySource.get(key);
            if (group.record.value !== record.value) throw Error('Conflicting source population: ' + key);
            group.record.approximate ||= record.approximate;
            group.record.reason ||= record.reason;
            group.polygons.push(...entry.polygons); group.geometryProvinces.add(entry.properties.province);
            group.parts.push(entry);
        }
        return [...bySource.values()];
    }
    function geometry(polygons, offset) {
        return !offset ? polygonPath(polygons) : polygons.map(poly => poly.map(ring => line(ring.map(point => { const p = screen(point); return [p[0] + offset[0], p[1] + offset[1]] })) + 'Z').join('')).join('');
    }
    function paths(selection, values, offset) {
        const nodes = selection.selectAll('path.district-fill').data(values, d => d.key).join('path')
            .attr('class', 'district-fill').attr('stroke', 'none').attr('fill-rule', 'evenodd')
            .attr('fill', group => color(group.record.value)).attr('d', group => geometry(group.polygons, offset))
            .attr('data-source-key', group => group.key)
            .attr('aria-label', group => `${group.record.label} ${fmt(group.record.value)}명`);
        nodes.on('pointermove', (event, group) => {
            const r = group.record;
            tooltip.textContent = `${r.label} · ${fmt(r.value)}명${r.approximate ? ' · 근사 경계' : ''}`;
            Object.assign(tooltip.style, { display: 'block', left: Math.max(8, Math.min(innerWidth - 300, event.clientX + 12)) + 'px', top: Math.min(innerHeight - 45, event.clientY + 16) + 'px' });
        }).on('pointerleave', () => tooltip.style.display = 'none')
            .on('click', (_, group) => selectRegion(group.record.province));
        return nodes;
    }
    return {
        max,
        update(year, detailed) {
            currentYear = year; active = detailed; groups = active ? groupRecords(year) : [];
            layer.style('display', active ? null : 'none');
            if (active) {
                paths(layer, groups);
                available.attr('d', groups.map(g => geometry(g.polygons)).join(''));
            }
            d3.select('#land').attr('clip-path', active ? 'url(#availableDistrictClip)' : null);
            d3.select('#gridLines').attr('clip-path', active ? 'url(#availableDistrictClip)' : 'url(#landClip)');
        },
        inset(node, group, dx, dy) {
            const inset = node.selectAll('g.inset-districts').data([group]).join('g').attr('class', 'inset-districts').attr('clip-path', 'url(#island-clip-' + group.id + ')').style('display', active ? null : 'none');
            const id = 'inset-available-' + group.id;
            const clip = node.selectAll('clipPath.inset-available').data([group]).join('clipPath').attr('class', 'inset-available').attr('id', id).attr('clip-path', 'url(#island-clip-' + group.id + ')');
            clip.selectAll('path').data([group]).join('path').attr('fill-rule', 'evenodd');
            if (active) {
                const values = groups.filter(g => g.geometryProvinces.has(group.region)).map(g => ({ ...g, polygons: g.parts.filter(p => p.properties.province === group.region).flatMap(p => p.polygons) }));
                paths(inset, values, [dx, dy]);
                clip.select('path').attr('d', values.map(g => geometry(g.polygons, [dx, dy])).join(''));
                node.node().insertBefore(inset.node(), node.select('.inset-land').node());
            }
            node.select('.inset-land').attr('clip-path', active ? 'url(#' + id + ')' : null);
            node.select('.inset-grid').attr('clip-path', active ? 'url(#' + id + ')' : 'url(#island-clip-' + group.id + ')');
        }
    };
};
