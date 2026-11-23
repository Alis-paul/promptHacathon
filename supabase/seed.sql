-- Seed data for departments
INSERT INTO public.departments (id, name, helpline, email, sla_hours, created_at)
VALUES
  (gen_random_uuid(), 'Roads', '+1-800-ROADS', 'roads@example.gov', 48, now()),
  (gen_random_uuid(), 'Water Supply', '+1-800-WATER', 'water@example.gov', 48, now()),
  (gen_random_uuid(), 'Drainage', '+1-800-DRNAGE', 'drainage@example.gov', 48, now()),
  (gen_random_uuid(), 'Sanitation', '+1-800-SANIT', 'sanitation@example.gov', 48, now()),
  (gen_random_uuid(), 'Electrical / Streetlights', '+1-800-LIGHTS', 'lights@example.gov', 48, now());
