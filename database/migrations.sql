--
-- PostgreSQL database dump
--

\restrict d4e7HHwVnZ5uPn6FiyetgMOF9K0rHDyvodikdANZwrMtCF4IcP2Nde3LMuhW9uU

-- Dumped from database version 17.6 (Debian 17.6-1.pgdg12+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.categories (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(100) DEFAULT NULL::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone
);


ALTER TABLE public.categories OWNER TO firefeed_db_usr;

--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.categories_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categories_id_seq OWNER TO firefeed_db_usr;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: news_translations; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.news_translations (
    id bigint NOT NULL,
    news_id character varying(255) NOT NULL,
    language character varying(10) NOT NULL,
    translated_title text NOT NULL,
    translated_content text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone
);


ALTER TABLE public.news_translations OWNER TO firefeed_db_usr;

--
-- Name: news_translations_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.news_translations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.news_translations_id_seq OWNER TO firefeed_db_usr;

--
-- Name: news_translations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.news_translations_id_seq OWNED BY public.news_translations.id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.password_reset_tokens (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    token text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.password_reset_tokens OWNER TO firefeed_db_usr;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.password_reset_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.password_reset_tokens_id_seq OWNER TO firefeed_db_usr;

--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;


--
-- Name: published_news_data; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.published_news_data (
    news_id character varying(255) NOT NULL,
    original_title text NOT NULL,
    original_content text NOT NULL,
    original_language character varying(10) NOT NULL,
    category_id bigint,
    image_filename character varying(255) DEFAULT NULL::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone,
    rss_feed_id bigint,
    embedding public.vector(384),
    source_url text,
    video_filename text
);


ALTER TABLE public.published_news_data OWNER TO firefeed_db_usr;

--
-- Name: rss_feeds; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.rss_feeds (
    id bigint NOT NULL,
    source_id bigint NOT NULL,
    url character varying(500) NOT NULL,
    name character varying(255) NOT NULL,
    category_id bigint,
    language character varying(10) NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone,
    cooldown_minutes integer DEFAULT 10,
    max_news_per_hour integer DEFAULT 10
);


ALTER TABLE public.rss_feeds OWNER TO firefeed_db_usr;

--
-- Name: rss_feeds_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.rss_feeds_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rss_feeds_id_seq OWNER TO firefeed_db_usr;

--
-- Name: rss_feeds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.rss_feeds_id_seq OWNED BY public.rss_feeds.id;


--
-- Name: rss_items_telegram_bot_published; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.rss_items_telegram_bot_published (
    id integer NOT NULL,
    news_id character varying(255),
    translation_id integer,
    recipient_type character varying(10) NOT NULL,
    recipient_id bigint NOT NULL,
    message_id bigint,
    language character varying(5),
    sent_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT rss_items_telegram_bot_published_recipient_type_check CHECK (((recipient_type)::text = ANY ((ARRAY['channel'::character varying, 'user'::character varying])::text[])))
);


ALTER TABLE public.rss_items_telegram_bot_published OWNER TO firefeed_db_usr;

--
-- Name: rss_items_telegram_bot_published_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.rss_items_telegram_bot_published_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rss_items_telegram_bot_published_id_seq OWNER TO firefeed_db_usr;

--
-- Name: rss_items_telegram_bot_published_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.rss_items_telegram_bot_published_id_seq OWNED BY public.rss_items_telegram_bot_published.id;


--
-- Name: source_categories; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.source_categories (
    source_id bigint NOT NULL,
    category_id bigint NOT NULL
);


ALTER TABLE public.source_categories OWNER TO firefeed_db_usr;

--
-- Name: sources; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.sources (
    id bigint NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone,
    alias character varying(255),
    logo character varying(500),
    site_url character varying(255)
);


ALTER TABLE public.sources OWNER TO firefeed_db_usr;

--
-- Name: sources_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.sources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sources_id_seq OWNER TO firefeed_db_usr;

--
-- Name: sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.sources_id_seq OWNED BY public.sources.id;


--
-- Name: user_api_keys; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.user_api_keys (
    id integer NOT NULL,
    user_id integer NOT NULL,
    key_hash text NOT NULL,
    limits jsonb DEFAULT '{"requests_per_day": 1000, "requests_per_hour": 100}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone
);


ALTER TABLE public.user_api_keys OWNER TO firefeed_db_usr;

--
-- Name: user_api_keys_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.user_api_keys_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_api_keys_id_seq OWNER TO firefeed_db_usr;

--
-- Name: user_api_keys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.user_api_keys_id_seq OWNED BY public.user_api_keys.id;


--
-- Name: user_categories; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.user_categories (
    user_id bigint NOT NULL,
    category_id integer NOT NULL
);


ALTER TABLE public.user_categories OWNER TO firefeed_db_usr;

--
-- Name: user_preferences; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.user_preferences (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    subscriptions text,
    language character varying(2) DEFAULT 'en'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_preferences OWNER TO firefeed_db_usr;

--
-- Name: user_preferences_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.user_preferences_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_preferences_id_seq OWNER TO firefeed_db_usr;

--
-- Name: user_preferences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.user_preferences_id_seq OWNED BY public.user_preferences.id;


--
-- Name: user_rss_feeds; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.user_rss_feeds (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    url character varying(500) NOT NULL,
    name character varying(255),
    category_id bigint,
    language character varying(10) DEFAULT 'en'::character varying,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_rss_feeds OWNER TO firefeed_db_usr;

--
-- Name: user_rss_feeds_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.user_rss_feeds_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_rss_feeds_id_seq OWNER TO firefeed_db_usr;

--
-- Name: user_rss_feeds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.user_rss_feeds_id_seq OWNED BY public.user_rss_feeds.id;


--
-- Name: user_telegram_links; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.user_telegram_links (
    id integer NOT NULL,
    user_id integer NOT NULL,
    telegram_id bigint,
    link_code character varying(32),
    created_at timestamp with time zone DEFAULT now(),
    linked_at timestamp with time zone,
    CONSTRAINT telegram_link_check CHECK ((((telegram_id IS NULL) AND (linked_at IS NULL)) OR ((telegram_id IS NOT NULL) AND (linked_at IS NOT NULL))))
);


ALTER TABLE public.user_telegram_links OWNER TO firefeed_db_usr;

--
-- Name: user_telegram_links_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.user_telegram_links_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_telegram_links_id_seq OWNER TO firefeed_db_usr;

--
-- Name: user_telegram_links_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.user_telegram_links_id_seq OWNED BY public.user_telegram_links.id;


--
-- Name: user_verification_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.user_verification_codes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_verification_codes_id_seq OWNER TO firefeed_db_usr;

--
-- Name: user_verification_codes; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.user_verification_codes (
    id bigint DEFAULT nextval('public.user_verification_codes_id_seq'::regclass) NOT NULL,
    user_id bigint NOT NULL,
    verification_code character varying(6) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone
);


ALTER TABLE public.user_verification_codes OWNER TO firefeed_db_usr;

--
-- Name: users; Type: TABLE; Schema: public; Owner: firefeed_db_usr
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    language character varying(2) DEFAULT 'en'::character varying,
    is_active boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_verified boolean DEFAULT false NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public.users OWNER TO firefeed_db_usr;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: firefeed_db_usr
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO firefeed_db_usr;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: firefeed_db_usr
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: news_translations id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.news_translations ALTER COLUMN id SET DEFAULT nextval('public.news_translations_id_seq'::regclass);


--
-- Name: password_reset_tokens id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq'::regclass);


--
-- Name: rss_feeds id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.rss_feeds ALTER COLUMN id SET DEFAULT nextval('public.rss_feeds_id_seq'::regclass);


--
-- Name: rss_items_telegram_bot_published id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.rss_items_telegram_bot_published ALTER COLUMN id SET DEFAULT nextval('public.rss_items_telegram_bot_published_id_seq'::regclass);


--
-- Name: sources id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.sources ALTER COLUMN id SET DEFAULT nextval('public.sources_id_seq'::regclass);


--
-- Name: user_api_keys id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_api_keys ALTER COLUMN id SET DEFAULT nextval('public.user_api_keys_id_seq'::regclass);


--
-- Name: user_preferences id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_preferences ALTER COLUMN id SET DEFAULT nextval('public.user_preferences_id_seq'::regclass);


--
-- Name: user_rss_feeds id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_rss_feeds ALTER COLUMN id SET DEFAULT nextval('public.user_rss_feeds_id_seq'::regclass);


--
-- Name: user_telegram_links id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_telegram_links ALTER COLUMN id SET DEFAULT nextval('public.user_telegram_links_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: categories idx_16802_primary; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT idx_16802_primary PRIMARY KEY (id);


--
-- Name: news_translations idx_16809_primary; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.news_translations
    ADD CONSTRAINT idx_16809_primary PRIMARY KEY (id);


--
-- Name: published_news_data idx_16825_primary; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.published_news_data
    ADD CONSTRAINT idx_16825_primary PRIMARY KEY (news_id);


--
-- Name: rss_feeds idx_16833_primary; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.rss_feeds
    ADD CONSTRAINT idx_16833_primary PRIMARY KEY (id);


--
-- Name: sources idx_16842_primary; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.sources
    ADD CONSTRAINT idx_16842_primary PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_key UNIQUE (token);


--
-- Name: rss_items_telegram_bot_published rss_items_telegram_bot_publis_news_id_translation_id_recipi_key; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.rss_items_telegram_bot_published
    ADD CONSTRAINT rss_items_telegram_bot_publis_news_id_translation_id_recipi_key UNIQUE (news_id, translation_id, recipient_type, recipient_id);


--
-- Name: rss_items_telegram_bot_published rss_items_telegram_bot_published_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.rss_items_telegram_bot_published
    ADD CONSTRAINT rss_items_telegram_bot_published_pkey PRIMARY KEY (id);


--
-- Name: source_categories source_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.source_categories
    ADD CONSTRAINT source_categories_pkey PRIMARY KEY (source_id, category_id);


--
-- Name: user_api_keys user_api_keys_key_hash_key; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_api_keys
    ADD CONSTRAINT user_api_keys_key_hash_key UNIQUE (key_hash);


--
-- Name: user_api_keys user_api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_api_keys
    ADD CONSTRAINT user_api_keys_pkey PRIMARY KEY (id);


--
-- Name: user_categories user_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_categories
    ADD CONSTRAINT user_categories_pkey PRIMARY KEY (user_id, category_id);


--
-- Name: user_preferences user_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (id);


--
-- Name: user_rss_feeds user_rss_feeds_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_rss_feeds
    ADD CONSTRAINT user_rss_feeds_pkey PRIMARY KEY (id);


--
-- Name: user_telegram_links user_telegram_links_link_code_key; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_telegram_links
    ADD CONSTRAINT user_telegram_links_link_code_key UNIQUE (link_code);


--
-- Name: user_telegram_links user_telegram_links_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_telegram_links
    ADD CONSTRAINT user_telegram_links_pkey PRIMARY KEY (id);


--
-- Name: user_telegram_links user_telegram_links_telegram_id_key; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_telegram_links
    ADD CONSTRAINT user_telegram_links_telegram_id_key UNIQUE (telegram_id);


--
-- Name: user_verification_codes user_verification_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_verification_codes
    ADD CONSTRAINT user_verification_codes_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_16802_unique_name; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE UNIQUE INDEX idx_16802_unique_name ON public.categories USING btree (name);


--
-- Name: idx_16809_idx_language; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_16809_idx_language ON public.news_translations USING btree (language);


--
-- Name: idx_16809_idx_news_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_16809_idx_news_id ON public.news_translations USING btree (news_id);


--
-- Name: idx_16809_unique_news_lang; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE UNIQUE INDEX idx_16809_unique_news_lang ON public.news_translations USING btree (news_id, language);


--
-- Name: idx_16825_fk_published_news_data_category_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_16825_fk_published_news_data_category_id ON public.published_news_data USING btree (category_id);


--
-- Name: idx_16825_idx_image_filename; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_16825_idx_image_filename ON public.published_news_data USING btree (image_filename);


--
-- Name: idx_16825_idx_original_language; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_16825_idx_original_language ON public.published_news_data USING btree (original_language);


--
-- Name: idx_16833_idx_category_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_16833_idx_category_id ON public.rss_feeds USING btree (category_id);


--
-- Name: idx_16833_idx_source_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_16833_idx_source_id ON public.rss_feeds USING btree (source_id);


--
-- Name: idx_16833_unique_feed; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE UNIQUE INDEX idx_16833_unique_feed ON public.rss_feeds USING btree (url);


--
-- Name: idx_16842_unique_name; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE UNIQUE INDEX idx_16842_unique_name ON public.sources USING btree (name);


--
-- Name: idx_news_translations_news_id_lang; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_news_translations_news_id_lang ON public.news_translations USING btree (news_id, language);


--
-- Name: idx_news_translations_news_id_language; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_news_translations_news_id_language ON public.news_translations USING btree (news_id, language);


--
-- Name: idx_news_translations_translated_content_trgm; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_news_translations_translated_content_trgm ON public.news_translations USING gin (translated_content public.gin_trgm_ops) WHERE (translated_content IS NOT NULL);


--
-- Name: idx_news_translations_translated_title_trgm; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_news_translations_translated_title_trgm ON public.news_translations USING gin (translated_title public.gin_trgm_ops) WHERE (translated_title IS NOT NULL);


--
-- Name: idx_password_reset_tokens_expires_at; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_password_reset_tokens_expires_at ON public.password_reset_tokens USING btree (expires_at);


--
-- Name: idx_password_reset_tokens_token; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE UNIQUE INDEX idx_password_reset_tokens_token ON public.password_reset_tokens USING btree (token);


--
-- Name: idx_password_reset_tokens_user_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_password_reset_tokens_user_id ON public.password_reset_tokens USING btree (user_id);


--
-- Name: idx_published_news_created_at; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_created_at ON public.published_news_data USING btree (created_at);


--
-- Name: idx_published_news_data_category_created_at; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_category_created_at ON public.published_news_data USING btree (category_id, created_at DESC);


--
-- Name: idx_published_news_data_category_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_category_id ON public.published_news_data USING btree (category_id);


--
-- Name: idx_published_news_data_content_gin; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_content_gin ON public.published_news_data USING gin (to_tsvector('english'::regconfig, original_content));


--
-- Name: idx_published_news_data_created_at; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_created_at ON public.published_news_data USING btree (created_at DESC);


--
-- Name: idx_published_news_data_created_at_desc; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_created_at_desc ON public.published_news_data USING btree (created_at DESC);


--
-- Name: idx_published_news_data_created_at_news_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_created_at_news_id ON public.published_news_data USING btree (created_at DESC, news_id);


--
-- Name: idx_published_news_data_embedding; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_embedding ON public.published_news_data USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_published_news_data_news_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_news_id ON public.published_news_data USING btree (news_id);


--
-- Name: idx_published_news_data_original_content_trgm; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_original_content_trgm ON public.published_news_data USING gin (original_content public.gin_trgm_ops) WHERE (original_content IS NOT NULL);


--
-- Name: idx_published_news_data_original_title_trgm; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_original_title_trgm ON public.published_news_data USING gin (original_title public.gin_trgm_ops) WHERE (original_title IS NOT NULL);


--
-- Name: idx_published_news_data_rss_feed_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_rss_feed_id ON public.published_news_data USING btree (rss_feed_id);


--
-- Name: idx_published_news_data_rss_feed_id_created_at; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_rss_feed_id_created_at ON public.published_news_data USING btree (rss_feed_id, created_at DESC);


--
-- Name: idx_published_news_data_title_gin; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_data_title_gin ON public.published_news_data USING gin (to_tsvector('english'::regconfig, original_title));


--
-- Name: idx_published_news_embedding; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_embedding ON public.published_news_data USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_published_news_rss_feed_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_published_news_rss_feed_id ON public.published_news_data USING btree (rss_feed_id);


--
-- Name: idx_rss_bot_published_news_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_rss_bot_published_news_id ON public.rss_items_telegram_bot_published USING btree (news_id);


--
-- Name: idx_rss_bot_published_recipient; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_rss_bot_published_recipient ON public.rss_items_telegram_bot_published USING btree (recipient_type, recipient_id);


--
-- Name: idx_rss_bot_published_sent_at; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_rss_bot_published_sent_at ON public.rss_items_telegram_bot_published USING btree (sent_at);


--
-- Name: idx_rss_bot_published_translation_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_rss_bot_published_translation_id ON public.rss_items_telegram_bot_published USING btree (translation_id);


--
-- Name: idx_rss_feeds_category_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_rss_feeds_category_id ON public.rss_feeds USING btree (category_id);


--
-- Name: idx_rss_feeds_is_active; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_rss_feeds_is_active ON public.rss_feeds USING btree (is_active);


--
-- Name: idx_rss_feeds_source_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_rss_feeds_source_id ON public.rss_feeds USING btree (source_id);


--
-- Name: idx_source_categories_source_id_category_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_source_categories_source_id_category_id ON public.source_categories USING btree (source_id, category_id);


--
-- Name: idx_user_api_keys_key_hash; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_api_keys_key_hash ON public.user_api_keys USING btree (key_hash);


--
-- Name: idx_user_api_keys_user_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_api_keys_user_id ON public.user_api_keys USING btree (user_id);


--
-- Name: idx_user_categories_category_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_categories_category_id ON public.user_categories USING btree (category_id);


--
-- Name: idx_user_categories_user_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_categories_user_id ON public.user_categories USING btree (user_id);


--
-- Name: idx_user_rss_feeds_category_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_rss_feeds_category_id ON public.user_rss_feeds USING btree (category_id);


--
-- Name: idx_user_rss_feeds_is_active; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_rss_feeds_is_active ON public.user_rss_feeds USING btree (is_active);


--
-- Name: idx_user_rss_feeds_user_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_rss_feeds_user_id ON public.user_rss_feeds USING btree (user_id);


--
-- Name: idx_user_rss_feeds_user_id_category_id_is_active; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_rss_feeds_user_id_category_id_is_active ON public.user_rss_feeds USING btree (user_id, category_id, is_active);


--
-- Name: idx_user_rss_feeds_user_url; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE UNIQUE INDEX idx_user_rss_feeds_user_url ON public.user_rss_feeds USING btree (user_id, url);


--
-- Name: idx_user_telegram_links_link_code; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_telegram_links_link_code ON public.user_telegram_links USING btree (link_code);


--
-- Name: idx_user_telegram_links_telegram_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_telegram_links_telegram_id ON public.user_telegram_links USING btree (telegram_id);


--
-- Name: idx_user_telegram_links_user_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_telegram_links_user_id ON public.user_telegram_links USING btree (user_id);


--
-- Name: idx_user_verification_codes_active; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_verification_codes_active ON public.user_verification_codes USING btree (verification_code, expires_at) WHERE (used_at IS NULL);


--
-- Name: idx_user_verification_codes_code; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_verification_codes_code ON public.user_verification_codes USING btree (verification_code);


--
-- Name: idx_user_verification_codes_expires_at; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_verification_codes_expires_at ON public.user_verification_codes USING btree (expires_at);


--
-- Name: idx_user_verification_codes_user_id; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_verification_codes_user_id ON public.user_verification_codes USING btree (user_id);


--
-- Name: idx_user_verification_codes_verification_code; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_user_verification_codes_verification_code ON public.user_verification_codes USING btree (verification_code);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE UNIQUE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_is_active; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_users_is_active ON public.users USING btree (is_active);


--
-- Name: idx_users_is_deleted; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_users_is_deleted ON public.users USING btree (is_deleted);


--
-- Name: idx_users_is_verified; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_users_is_verified ON public.users USING btree (is_verified);


--
-- Name: idx_users_is_verified_is_deleted; Type: INDEX; Schema: public; Owner: firefeed_db_usr
--

CREATE INDEX idx_users_is_verified_is_deleted ON public.users USING btree (is_verified, is_deleted);


--
-- Name: rss_feeds fk_feeds_category_id; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.rss_feeds
    ADD CONSTRAINT fk_feeds_category_id FOREIGN KEY (category_id) REFERENCES public.categories(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: published_news_data fk_published_news_data_category_id; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.published_news_data
    ADD CONSTRAINT fk_published_news_data_category_id FOREIGN KEY (category_id) REFERENCES public.categories(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: news_translations fk_translations_news_id; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.news_translations
    ADD CONSTRAINT fk_translations_news_id FOREIGN KEY (news_id) REFERENCES public.published_news_data(news_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: source_categories source_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.source_categories
    ADD CONSTRAINT source_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;


--
-- Name: source_categories source_categories_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.source_categories
    ADD CONSTRAINT source_categories_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.sources(id) ON DELETE CASCADE;


--
-- Name: user_api_keys user_api_keys_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_api_keys
    ADD CONSTRAINT user_api_keys_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_categories user_categories_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_categories
    ADD CONSTRAINT user_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;


--
-- Name: user_categories user_categories_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_categories
    ADD CONSTRAINT user_categories_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_preferences user_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_rss_feeds user_rss_feeds_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_rss_feeds
    ADD CONSTRAINT user_rss_feeds_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE SET NULL;


--
-- Name: user_rss_feeds user_rss_feeds_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_rss_feeds
    ADD CONSTRAINT user_rss_feeds_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_telegram_links user_telegram_links_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_telegram_links
    ADD CONSTRAINT user_telegram_links_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_verification_codes user_verification_codes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: firefeed_db_usr
--

ALTER TABLE ONLY public.user_verification_codes
    ADD CONSTRAINT user_verification_codes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO firefeed_db_grp;


--
-- PostgreSQL database dump complete
--

\unrestrict d4e7HHwVnZ5uPn6FiyetgMOF9K0rHDyvodikdANZwrMtCF4IcP2Nde3LMuhW9uU
