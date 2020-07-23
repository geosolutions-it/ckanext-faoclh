const location_id = localStorage.getItem('fao_facet_scroll_location');
const element_in_view = document.getElementById(location_id);
if (element_in_view){
    const elementRect = element_in_view.getBoundingClientRect();
    const absoluteElementTop = elementRect.top + window.pageYOffset;
    const middle = absoluteElementTop - (window.innerHeight / 2);
    window.scrollTo(0, middle);
}
const fao_facet_search_key = '_fao_expanded_facets';

function update_facet_href(elements = [], open_facet_href) {
	const arrayLength = elements.length;
	for (let i = 0; i < arrayLength; i++) {
		const href_search_params = new window.URLSearchParams(elements[i].search);
		href_search_params.set(fao_facet_search_key, open_facet_href);
		elements[i].href = `?${href_search_params.toString()}`;
	}
}
async function toggle_facet_expansion_url_params(facet) {
	const params = new window.URLSearchParams(window.location.search);
	let all_facet_links = document.getElementsByClassName('fao-facet-link');
	try {
		let open_facets = [...new Set(params.get(fao_facet_search_key).split(','))];
		if (!document.getElementById(`${facet}_facet`).classList.contains('faoclh-collapsible-nav') && open_facets.includes(facet)) {
			const new_open_facets = open_facets.filter(function (item) {
				return item !== facet
			});
			params.set(fao_facet_search_key, new_open_facets.join(','));
			window.history.replaceState(null, null, `?${params.toString()}`);
			await update_facet_href(all_facet_links, params.get(fao_facet_search_key));
		} else {
			open_facets.push(facet);
			params.set(fao_facet_search_key, open_facets.join(','));
			window.history.replaceState(null, null, `?${params.toString()}`);
			await update_facet_href(all_facet_links, params.get(fao_facet_search_key));
		}
	} catch (e) {
	    // only catch TypeError that can possible arise when url does not contain the `_fao_expanded_facets` search key
		if (e instanceof TypeError) {
			params.set(fao_facet_search_key, facet);
			window.history.replaceState(null, null, `?${params.toString()}`);
			await update_facet_href(all_facet_links, params.get(fao_facet_search_key));
		} else {
			throw e;
		}
	}
}