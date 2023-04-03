export interface Event {
	id: number;
	name: string;
	creator: User;
	host: User;
	created_at: Date;
	updated_at: Date;
	description: string;
	description_attribute: string;
	tz: string;
	event_dates: MiniEventDate[];
	next_date: EventDate;
	event_tags: EventTag[];
	rrule: Rrule;
	media_items: MediaItem[];
	cover_items: MediaItem[];
	hidden: boolean;
	last_transaction: Transaction;
	is_favorited: boolean;
	page_views: number;
}

export interface EventVersion {
	id: number;
	name: string;
	creator: User;
	host: User;
	created_at: Date;
	updated_at: Date;
	description: string;
	description_attribute: string;
	tz: string;
	event_dates: EventDate[];
	next_date: EventDate;
	event_tags: EventTag[];
	rrule: Rrule;
	media_items: MediaItem[];
	cover_items: MediaItem[];
	hidden: boolean;
	last_transaction: Transaction;
	is_favorited: boolean;
	page_views: number;
	changeset: object;
	index: number;
	transaction: Transaction;
	transaction_id: number;
	end_transaction_id: number;
}

export interface Rrule {
	recurring_type: number;
	separation_count: number;
	day_of_week: number;
	week_of_month: number;
	day_of_month: number;
	month_of_year: number;
	start_date_time: string;
	end_date_time: string;
}

export interface RruleVersion {
	recurring_type: number;
	separation_count: number;
	day_of_week: number;
	week_of_month: number;
	day_of_month: number;
	month_of_year: number;
	start_date_time: string;
	end_date_time: string;
	changeset: object;
	index: number;
	transaction: Transaction;
	transaction_id: number;
	end_transaction_id: number;
}

export interface OAuth {
	provider_user_id: string;
	user_id: string;
	created_at: Date;
	token: object;
}

export interface User {
	username: string;
	role: number;
	id: string;
	version_count: number;
	hosted_events: Event[];
	created_events: Event[];
	created_at: Date;
}

export interface PrivateUser {
	username: string;
	role: number;
	id: string;
	version_count: number;
	hosted_events: Event[];
	created_events: Event[];
	created_at: Date;
	email: string;
	status: string;
	pw_enabled: any;
	oauth: boolean;
	oauth_obj: OAuth;
	last_active: Date;
}

export interface Tag {
	tag: string;
	count: number;
}

export interface EventTag {
	tag: string;
}

export interface EventDate {
	id: number;
	event_id: number;
	name: string;
	start: string;
	end: string;
	start_naive: string;
	end_naive: string;
	tz: string;
	location: Location;
	location_id: string;
	event: Event;
	description: string;
	description_attribute: string;
	url: string;
	ticket_url: string;
	cancelled: boolean;
	distance: number;
	duration: number;
	size: number;
	artists: EventDateArtist[];
}

export interface MiniEventDate {
	id: number;
	event_id: number;
	start: string;
	end: string;
	start_naive: string;
	end_naive: string;
	tz: string;
}

export interface EventDateVersion {
	id: number;
	event_id: number;
	name: string;
	start: string;
	end: string;
	start_naive: string;
	end_naive: string;
	tz: string;
	location: Location;
	location_id: string;
	event: Event;
	description: string;
	description_attribute: string;
	url: string;
	ticket_url: string;
	cancelled: boolean;
	distance: number;
	duration: number;
	size: number;
	artists: EventDateArtist[];
	changeset: object;
	previous: EventDateVersion;
	index: number;
	transaction: Transaction;
	transaction_id: number;
	end_transaction_id: number;
}

export interface Artist {
	id: number;
	name: string;
	area: string;
	mbid: string;
	description: string;
	popularity: number;
	disambiguation: string;
	urls: ArtistUrl[];
	tags: ArtistTag[];
	future_event_dates: EventDate[];
	past_event_dates: EventDate[];
	event_count: number;
	media_items: MediaItem[];
}

export interface ArtistUrl {
	url: string;
	type: string;
}

export interface ArtistTag {
	tag: string;
}

export interface EventDateArtist {
	description: any;
	disambiguation: any;
	name: any;
	popularity: any;
	area: any;
	mbid: any;
	urls: any;
	media_items: any;
	artist_id: any;
	id: number;
	start_naive: string;
	stage: string;
}

export interface MediaItem {
	id: string;
	creator: User;
	created_at: Date;
	filename: string;
	position: number;
	duration: number;
	caption: string;
	type: string;
	image_url: any;
	image_med_url: any;
	v_low_url: any;
	v_med_url: any;
	v_high_url: any;
	thumb_url: any;
	thumb_xs_url: any;
	thumb_xxs_url: any;
	poster_url: any;
}

export interface MediaItemVersion {
	id: string;
	creator: User;
	created_at: Date;
	filename: string;
	position: number;
	duration: number;
	caption: string;
	type: string;
	image_url: any;
	image_med_url: any;
	v_low_url: any;
	v_med_url: any;
	v_high_url: any;
	thumb_url: any;
	thumb_xs_url: any;
	thumb_xxs_url: any;
	poster_url: any;
	changeset: object;
	previous: MediaItemVersion;
	index: number;
	transaction: Transaction;
	transaction_id: number;
	end_transaction_id: number;
}

export interface Transaction {
	id: number;
	issued_at: Date;
	user: User;
}

export interface Activity {
	id: number;
	actor: User;
	transaction: Transaction;
	changeset: object;
	verb: string;
	object_type: string;
	object_version: any;
	target_version: any;
	previous_version: any;
	previous_target_version: any;
	target_version_tx_id: number;
	version_index: number;
	data: object;
}

export interface Location {
	geohash: string;
	lat: number;
	lng: number;
	name: string;
	description: string;
	locality: Locality;
	country: string;
	city: string;
	address_components: string;
	place_id: string;
	event_dates: EventDate[];
}

export interface Locality {
	id: string;
	short_name: string;
	long_name: string;
	country: Country;
	region: Region;
}

export interface Region {
	id: string;
	short_name: string;
	long_name: string;
	country: Country;
	localities: Locality[];
}

export interface Country {
	short_name: string;
	long_name: string;
	regions: Region[];
}

export interface Point {
	place_id: string;
	lat: number;
	lng: number;
	name: string;
	events: any[];
}

export interface Report {
	id: string;
	creator: PrivateUser;
	created_at: Date;
	open: boolean;
	message: string;
	email: string;
	event: Event;
	event_contribution: EventContribution;
	media_item: MediaItem;
}

export interface SuggestedEdit {
	id: number;
	created_at: Date;
	creator: User;
	event_date_id: number;
	event_id: number;
	action: string;
	kwargs: object;
	message: string;
	object_type: string;
	status: string;
	approved_by: User;
}

export interface SuggestedEditList {
	has_next: boolean;
	has_prev: boolean;
	page: number;
	pages: number;
	per_page: number;
	next_num: number;
	prev_num: number;
	total: number;
	items: SuggestedEdit[];
}

export interface EventContribution {
	id: string;
	event_id: number;
	text: string;
	images: AlbumItem[];
	creator: User;
	created_at: Date;
	score: number;
}

