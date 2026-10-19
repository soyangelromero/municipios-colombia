-- Un apoyo = una persona (hash de IP) que pide un dato de un municipio. No guarda texto ni contacto.
CREATE TABLE IF NOT EXISTS apoyos (
  municipio TEXT NOT NULL,
  dato TEXT NOT NULL,
  ip_hash TEXT NOT NULL,
  creado TEXT NOT NULL,
  PRIMARY KEY (municipio, dato, ip_hash)
);
CREATE INDEX IF NOT EXISTS apoyos_ip ON apoyos (ip_hash, creado);
CREATE INDEX IF NOT EXISTS apoyos_creado ON apoyos (creado);
