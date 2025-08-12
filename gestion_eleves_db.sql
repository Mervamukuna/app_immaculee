-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : lun. 04 août 2025 à 17:55
-- Version du serveur : 10.4.32-MariaDB
-- Version de PHP : 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `gestion_eleves_db`
--

-- --------------------------------------------------------

--
-- Structure de la table `achats_articles`
--

CREATE TABLE `achats_articles` (
  `id` int(11) NOT NULL,
  `matricule` varchar(255) NOT NULL,
  `code_article` varchar(255) NOT NULL,
  `quantite` int(11) NOT NULL,
  `prix_unitaire` decimal(10,2) NOT NULL,
  `date_achat` varchar(50) NOT NULL,
  `caissier` varchar(255) DEFAULT NULL,
  `total` decimal(12,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `achats_articles`
--

INSERT INTO `achats_articles` (`id`, `matricule`, `code_article`, `quantite`, `prix_unitaire`, `date_achat`, `caissier`, `total`) VALUES
(1, 'MBM-1-2026', '001', 1, 10.00, '2025-07-23', 'Lombe Father', 10.00);

-- --------------------------------------------------------

--
-- Structure de la table `articles`
--

CREATE TABLE `articles` (
  `id` int(11) NOT NULL,
  `code` varchar(255) NOT NULL,
  `nom` varchar(255) NOT NULL,
  `prix` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `articles`
--

INSERT INTO `articles` (`id`, `code`, `nom`, `prix`) VALUES
(1, '001', 'TENUE EPS', 10.00);

-- --------------------------------------------------------

--
-- Structure de la table `classes`
--

CREATE TABLE `classes` (
  `id` int(11) NOT NULL,
  `nom` varchar(255) NOT NULL,
  `section_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `classes`
--

INSERT INTO `classes` (`id`, `nom`, `section_id`) VALUES
(1, '1ère Maternelle A', 1),
(2, '1ère Maternelle B', 1),
(3, '2ème Maternelle A', 1),
(4, '2ème Maternelle B', 1),
(5, '3ème Maternelle A', 1),
(6, '3ème Maternelle B', 1),
(7, '1ère Primaire A', 2),
(8, '1ère Primaire B', 2),
(9, '1ère Primaire C', 2),
(10, '2ème Primaire A', 2),
(11, '2ème Primaire B', 2),
(12, '2ème Primaire C', 2),
(13, '3ème Primaire A', 2),
(14, '3ème Primaire B', 2),
(15, '3ème Primaire C', 2),
(16, '4ème Primaire A', 2),
(17, '4ème Primaire B', 2),
(18, '4ème Primaire C', 2),
(19, '5ème Primaire A', 2),
(20, '5ème Primaire B', 2),
(21, '5ème Primaire C', 2),
(22, '6ème Primaire A', 2),
(23, '6ème Primaire B', 2),
(24, '6ème Primaire C', 2),
(25, '7ème A', 3),
(26, '7ème B', 3),
(27, '7ème C', 3),
(28, '8ème A', 3),
(29, '8ème B', 3),
(30, '8ème C', 3),
(31, '1ère Commerciale de Gestion', 3),
(32, '1ère Électricité', 3),
(33, '1ère Humanité Pédagogique', 3),
(34, '1ère Latin Philo', 3),
(35, '1ère Mécanique Générale', 3),
(36, '1ère Technique Coupe et Couture', 3),
(37, '1ère Scientifique', 3),
(38, '2ème Commerciale de Gestion', 3),
(39, '2ème Électricité', 3),
(40, '2ème Humanité Pédagogique', 3),
(41, '2ème Latin Philo', 3),
(42, '2ème Mécanique Générale', 3),
(43, '2ème Technique Coupe et Couture', 3),
(44, '2ème Scientifique', 3),
(45, '3ème Commerciale de Gestion', 3),
(46, '3ème Électricité', 3),
(47, '3ème Humanité Pédagogique', 3),
(48, '3ème Latin Philo', 3),
(49, '3ème Mécanique Générale', 3),
(50, '3ème Technique Coupe et Couture', 3),
(51, '3ème Scientifique', 3),
(52, '4ème Commerciale de Gestion', 3),
(53, '4ème Électricité', 3),
(54, '4ème Humanité Pédagogique', 3),
(55, '4ème Latin Philo', 3),
(56, '4ème Mécanique Générale', 3),
(57, '4ème Technique Coupe et Couture', 3),
(58, '4ème Scientifique', 3),
(60, '1ère Mécanique Automobile', 3),
(61, '2ème Mécanique Automobile', 3),
(62, '3ème Mécanique Automobile', 3),
(63, '4ème Mécanique Automobile', 3);

-- --------------------------------------------------------

--
-- Structure de la table `eleves`
--

CREATE TABLE `eleves` (
  `id` int(11) NOT NULL,
  `matricule` varchar(100) NOT NULL,
  `nom` varchar(255) NOT NULL,
  `postnom` varchar(255) NOT NULL,
  `prenom` varchar(255) NOT NULL,
  `genre` varchar(50) NOT NULL,
  `section` varchar(100) NOT NULL,
  `classe` varchar(100) NOT NULL,
  `annee_scolaire` varchar(50) NOT NULL,
  `date_inscription` varchar(50) NOT NULL,
  `lieu_naissance` varchar(255) DEFAULT NULL,
  `date_naissance` varchar(50) DEFAULT NULL,
  `ecole_provenance` varchar(255) DEFAULT NULL,
  `classe_precedente` varchar(100) DEFAULT NULL,
  `responsable` varchar(255) NOT NULL,
  `telephone_responsable` varchar(50) NOT NULL,
  `fonction_responsable` varchar(100) DEFAULT NULL,
  `statut_eleve` varchar(50) DEFAULT NULL,
  `frais_inscription` varchar(50) NOT NULL,
  `ram_papier` varchar(50) DEFAULT NULL,
  `frais_bulletin` varchar(50) DEFAULT NULL,
  `deux_savons` varchar(50) DEFAULT NULL,
  `deux_ph` varchar(50) DEFAULT NULL,
  `fournitures` varchar(255) DEFAULT NULL,
  `adresse` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `eleves`
--

INSERT INTO `eleves` (`id`, `matricule`, `nom`, `postnom`, `prenom`, `genre`, `section`, `classe`, `annee_scolaire`, `date_inscription`, `lieu_naissance`, `date_naissance`, `ecole_provenance`, `classe_precedente`, `responsable`, `telephone_responsable`, `fonction_responsable`, `statut_eleve`, `frais_inscription`, `ram_papier`, `frais_bulletin`, `deux_savons`, `deux_ph`, `fournitures`, `adresse`) VALUES
(1, 'MBM-1-2026', 'MUKUNA', 'BANGI', 'MERVEILLE', 'Masculin', 'Maternelle', '1ère Maternelle A', '2025-2026', '2025-07-23', 'LUBUMBASHI', '2025-02-28', 'C.S.BEL', '1ere Maternelle', 'MUKUNA BANGI', '+243811329047', 'LIBERALE', 'Nouveau', '45', 'Non', '5000', 'Non', 'Non', '50', '23/des mines/Craa/Kampemba'),
(2, 'MMI-2-2026', 'MUKONKI', 'MWEWA', 'IGNACE', 'Féminin', 'Primaire', '1ère Primaire A', '2025-2026', '2025-07-23', 'LIKASI', '2025-07-23', '', '2eme Primaire', 'MUKUNA JEAN', '+243992299222', 'AGENT SNCC', 'Ancien', '40', 'Oui', '5000', 'Oui', 'Non', '', '23/des mines/Craa/Kampemba'),
(3, 'MKM-3-2026', 'MUKOPA ', 'KIBALE', 'MEDARD', 'Masculin', 'Secondaire', '4ème Mécanique Générale', '2025-2026', '2025-07-23', 'LUBUMBASHI', '2025-07-23', 'IMARA', '2E MATERNEL', 'PAUL', '+2438888888', 'AGENT GECAMINES', 'Ancien', '150', 'Oui', '5000', 'Non', 'Oui', '', '23/des mines/Craa/Kampemba');

-- --------------------------------------------------------

--
-- Structure de la table `frais_etat`
--

CREATE TABLE `frais_etat` (
  `id` int(11) NOT NULL,
  `matricule` varchar(255) NOT NULL,
  `tranche` varchar(255) NOT NULL,
  `montant` decimal(12,2) NOT NULL,
  `date_paiement` varchar(50) NOT NULL,
  `mode_paiement` varchar(255) DEFAULT NULL,
  `annee_scolaire` varchar(50) DEFAULT NULL,
  `caissier` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `frais_etat`
--

INSERT INTO `frais_etat` (`id`, `matricule`, `tranche`, `montant`, `date_paiement`, `mode_paiement`, `annee_scolaire`, `caissier`) VALUES
(1, 'MBM-1-2026', 'Tranche 1', 10000.00, '2025-07-23', NULL, '2025-2026', 'Lombe Father');

-- --------------------------------------------------------

--
-- Structure de la table `paiements`
--

CREATE TABLE `paiements` (
  `id` int(11) NOT NULL,
  `matricule` varchar(255) NOT NULL,
  `mois` varchar(50) NOT NULL,
  `montant_paye` decimal(12,2) NOT NULL,
  `montant_a_payer` decimal(12,2) NOT NULL,
  `date_paiement` varchar(50) NOT NULL,
  `mode_paiement` varchar(255) DEFAULT NULL,
  `observation` text DEFAULT NULL,
  `annee_scolaire` varchar(50) NOT NULL,
  `montant_restant` decimal(12,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `paiements`
--

INSERT INTO `paiements` (`id`, `matricule`, `mois`, `montant_paye`, `montant_a_payer`, `date_paiement`, `mode_paiement`, `observation`, `annee_scolaire`, `montant_restant`) VALUES
(1, 'MBM-1-2026', 'Septembre', 30.00, 45.00, '2025-07-23', 'Cash', 'Lombe Father', '2025-2026', 15.00),
(2, 'MMI-2-2026', 'Septembre', 45.00, 45.00, '2025-07-23', 'Cash', 'Lombe Father', '2025-2026', 0.00),
(3, 'MBM-1-2026', 'Septembre', 10.00, 45.00, '2025-07-23', 'Cash', 'Lombe Father', '2025-2026', NULL),
(4, 'MBM-1-2026', 'Septembre', 1.00, 45.00, '2025-07-23', 'Cash', 'Lombe Father', '2025-2026', NULL);

-- --------------------------------------------------------

--
-- Structure de la table `sections`
--

CREATE TABLE `sections` (
  `id` int(11) NOT NULL,
  `nom` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `sections`
--

INSERT INTO `sections` (`id`, `nom`) VALUES
(1, 'Maternelle'),
(2, 'Primaire'),
(3, 'Secondaire');

-- --------------------------------------------------------

--
-- Structure de la table `tarifs`
--

CREATE TABLE `tarifs` (
  `id` int(11) NOT NULL,
  `classe_id` int(11) NOT NULL,
  `type` varchar(255) NOT NULL,
  `montant` int(11) NOT NULL,
  `statut_eleve` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `tarifs`
--

INSERT INTO `tarifs` (`id`, `classe_id`, `type`, `montant`, `statut_eleve`) VALUES
(1, 1, 'minerval', 45, ''),
(2, 2, 'minerval', 45, ''),
(3, 3, 'minerval', 45, ''),
(4, 4, 'minerval', 45, ''),
(5, 5, 'minerval', 45, ''),
(6, 6, 'minerval', 45, ''),
(7, 7, 'Minerval', 45, ''),
(8, 8, 'Minerval', 45, ''),
(9, 9, 'Minerval', 45, ''),
(10, 10, 'Minerval', 45, ''),
(11, 11, 'Minerval', 45, ''),
(12, 12, 'Minerval', 45, ''),
(13, 13, 'Minerval', 45, ''),
(14, 14, 'Minerval', 45, ''),
(15, 15, 'Minerval', 45, ''),
(16, 16, 'Minerval', 45, ''),
(17, 17, 'Minerval', 45, ''),
(18, 18, 'Minerval', 45, ''),
(19, 19, 'Minerval', 50, ''),
(20, 20, 'Minerval', 50, ''),
(21, 21, 'Minerval', 50, ''),
(22, 22, 'Minerval', 50, ''),
(23, 23, 'Minerval', 50, ''),
(24, 24, 'Minerval', 50, ''),
(25, 25, 'Minerval', 45, ''),
(26, 26, 'Minerval', 45, ''),
(27, 27, 'Minerval', 45, ''),
(28, 28, 'Minerval', 45, ''),
(29, 29, 'Minerval', 45, ''),
(30, 30, 'Minerval', 45, ''),
(31, 31, 'Minerval', 52, ''),
(32, 32, 'Minerval', 52, ''),
(33, 33, 'Minerval', 45, ''),
(34, 34, 'Minerval', 45, ''),
(35, 35, 'Minerval', 52, ''),
(36, 36, 'Minerval', 52, ''),
(37, 37, 'Minerval', 45, ''),
(38, 38, 'Minerval', 52, ''),
(39, 39, 'Minerval', 52, ''),
(40, 40, 'Minerval', 45, ''),
(41, 41, 'Minerval', 45, ''),
(42, 42, 'Minerval', 52, ''),
(43, 43, 'Minerval', 52, ''),
(44, 44, 'Minerval', 45, ''),
(45, 45, 'Minerval', 52, ''),
(46, 46, 'Minerval', 52, ''),
(47, 47, 'Minerval', 45, ''),
(48, 48, 'Minerval', 45, ''),
(49, 49, 'Minerval', 52, ''),
(50, 50, 'Minerval', 52, ''),
(51, 51, 'Minerval', 45, ''),
(52, 52, 'Minerval', 85, ''),
(53, 53, 'Minerval', 85, ''),
(54, 54, 'Minerval', 85, ''),
(55, 55, 'Minerval', 85, ''),
(56, 56, 'Minerval', 85, ''),
(57, 57, 'Minerval', 85, ''),
(58, 58, 'Minerval', 85, ''),
(59, 1, 'inscription', 40, 'ancien'),
(60, 2, 'inscription', 40, 'ancien'),
(61, 3, 'inscription', 40, 'ancien'),
(62, 4, 'inscription', 40, 'ancien'),
(63, 5, 'inscription', 40, 'ancien'),
(64, 6, 'inscription', 40, 'ancien'),
(65, 7, 'inscription', 40, 'ancien'),
(66, 8, 'inscription', 40, 'ancien'),
(67, 9, 'inscription', 40, 'ancien'),
(68, 10, 'inscription', 40, 'ancien'),
(69, 11, 'inscription', 40, 'ancien'),
(70, 12, 'inscription', 40, 'ancien'),
(71, 13, 'inscription', 40, 'ancien'),
(72, 14, 'inscription', 40, 'ancien'),
(73, 15, 'inscription', 40, 'ancien'),
(74, 16, 'inscription', 40, 'ancien'),
(75, 17, 'inscription', 40, 'ancien'),
(76, 18, 'inscription', 40, 'ancien'),
(77, 19, 'inscription', 40, 'ancien'),
(78, 20, 'inscription', 40, 'ancien'),
(79, 21, 'inscription', 40, 'ancien'),
(80, 22, 'inscription', 40, 'ancien'),
(81, 23, 'inscription', 40, 'ancien'),
(82, 24, 'inscription', 40, 'ancien'),
(83, 25, 'inscription', 40, 'ancien'),
(84, 26, 'inscription', 40, 'ancien'),
(85, 27, 'inscription', 40, 'ancien'),
(86, 28, 'inscription', 40, 'ancien'),
(87, 29, 'inscription', 40, 'ancien'),
(88, 30, 'inscription', 40, 'ancien'),
(89, 31, 'inscription', 40, 'ancien'),
(90, 32, 'inscription', 40, 'ancien'),
(91, 33, 'inscription', 40, 'ancien'),
(92, 34, 'inscription', 40, 'ancien'),
(93, 35, 'inscription', 40, 'ancien'),
(94, 36, 'inscription', 40, 'ancien'),
(95, 37, 'inscription', 40, 'ancien'),
(96, 38, 'inscription', 40, 'ancien'),
(97, 39, 'inscription', 40, 'ancien'),
(98, 40, 'inscription', 40, 'ancien'),
(99, 41, 'inscription', 40, 'ancien'),
(100, 42, 'inscription', 40, 'ancien'),
(101, 43, 'inscription', 40, 'ancien'),
(102, 44, 'inscription', 40, 'ancien'),
(103, 45, 'inscription', 40, 'ancien'),
(104, 46, 'inscription', 40, 'ancien'),
(105, 47, 'inscription', 40, 'ancien'),
(106, 48, 'inscription', 40, 'ancien'),
(107, 49, 'inscription', 40, 'ancien'),
(108, 50, 'inscription', 40, 'ancien'),
(109, 51, 'inscription', 40, 'ancien'),
(110, 1, 'inscription', 45, 'nouveau'),
(111, 2, 'inscription', 45, 'nouveau'),
(112, 3, 'inscription', 45, 'nouveau'),
(113, 4, 'inscription', 45, 'nouveau'),
(114, 5, 'inscription', 45, 'nouveau'),
(115, 6, 'inscription', 45, 'nouveau'),
(116, 7, 'inscription', 45, 'nouveau'),
(117, 8, 'inscription', 45, 'nouveau'),
(118, 9, 'inscription', 45, 'nouveau'),
(119, 10, 'inscription', 45, 'nouveau'),
(120, 11, 'inscription', 45, 'nouveau'),
(121, 12, 'inscription', 45, 'nouveau'),
(122, 13, 'inscription', 45, 'nouveau'),
(123, 14, 'inscription', 45, 'nouveau'),
(124, 15, 'inscription', 45, 'nouveau'),
(125, 16, 'inscription', 45, 'nouveau'),
(126, 17, 'inscription', 45, 'nouveau'),
(127, 18, 'inscription', 45, 'nouveau'),
(128, 19, 'inscription', 45, 'nouveau'),
(129, 20, 'inscription', 45, 'nouveau'),
(130, 21, 'inscription', 45, 'nouveau'),
(131, 22, 'inscription', 45, 'nouveau'),
(132, 23, 'inscription', 45, 'nouveau'),
(133, 24, 'inscription', 45, 'nouveau'),
(134, 25, 'inscription', 45, 'nouveau'),
(135, 26, 'inscription', 45, 'nouveau'),
(136, 27, 'inscription', 45, 'nouveau'),
(137, 28, 'inscription', 45, 'nouveau'),
(138, 29, 'inscription', 45, 'nouveau'),
(139, 30, 'inscription', 45, 'nouveau'),
(140, 31, 'inscription', 45, 'nouveau'),
(141, 32, 'inscription', 45, 'nouveau'),
(142, 33, 'inscription', 45, 'nouveau'),
(143, 34, 'inscription', 45, 'nouveau'),
(144, 35, 'inscription', 45, 'nouveau'),
(145, 36, 'inscription', 45, 'nouveau'),
(146, 37, 'inscription', 45, 'nouveau'),
(147, 38, 'inscription', 45, 'nouveau'),
(148, 39, 'inscription', 45, 'nouveau'),
(149, 40, 'inscription', 45, 'nouveau'),
(150, 41, 'inscription', 45, 'nouveau'),
(151, 42, 'inscription', 45, 'nouveau'),
(152, 43, 'inscription', 45, 'nouveau'),
(153, 44, 'inscription', 45, 'nouveau'),
(154, 45, 'inscription', 45, 'nouveau'),
(155, 46, 'inscription', 45, 'nouveau'),
(156, 47, 'inscription', 45, 'nouveau'),
(157, 48, 'inscription', 45, 'nouveau'),
(158, 49, 'inscription', 45, 'nouveau'),
(159, 50, 'inscription', 45, 'nouveau'),
(160, 51, 'inscription', 45, 'nouveau'),
(161, 52, 'inscription', 150, 'ancien'),
(162, 53, 'inscription', 150, 'ancien'),
(163, 54, 'inscription', 150, 'ancien'),
(164, 55, 'inscription', 150, 'ancien'),
(165, 56, 'inscription', 150, 'ancien'),
(166, 57, 'inscription', 150, 'ancien'),
(167, 58, 'inscription', 150, 'ancien'),
(168, 52, 'inscription', 200, 'nouveau'),
(169, 53, 'inscription', 200, 'nouveau'),
(170, 54, 'inscription', 200, 'nouveau'),
(171, 55, 'inscription', 200, 'nouveau'),
(172, 56, 'inscription', 200, 'nouveau'),
(173, 57, 'inscription', 200, 'nouveau'),
(174, 58, 'inscription', 200, 'nouveau');

-- --------------------------------------------------------

--
-- Structure de la table `utilisateurs`
--

CREATE TABLE `utilisateurs` (
  `id` int(11) NOT NULL,
  `nom` varchar(255) NOT NULL,
  `prenom` varchar(255) NOT NULL,
  `mot_de_passe` varchar(255) NOT NULL,
  `role` varchar(255) NOT NULL,
  `date_creation` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Déchargement des données de la table `utilisateurs`
--

INSERT INTO `utilisateurs` (`id`, `nom`, `prenom`, `mot_de_passe`, `role`, `date_creation`) VALUES
(1, 'Lombe', 'Father', 'scrypt:32768:8:1$2OzV1dI2SoW5QLVe$594886b7e33b4e7ff31d07654bc7e4055bb95da84b52029e2235da270cfc8f7c85feb5ab30cd4f410b301d80981dfc33ec093d06392f34d8313733484d43979e', 'full', '2025-07-21 23:43:13');

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `achats_articles`
--
ALTER TABLE `achats_articles`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `articles`
--
ALTER TABLE `articles`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `classes`
--
ALTER TABLE `classes`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `eleves`
--
ALTER TABLE `eleves`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `frais_etat`
--
ALTER TABLE `frais_etat`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `paiements`
--
ALTER TABLE `paiements`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `sections`
--
ALTER TABLE `sections`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `tarifs`
--
ALTER TABLE `tarifs`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `utilisateurs`
--
ALTER TABLE `utilisateurs`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `achats_articles`
--
ALTER TABLE `achats_articles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `articles`
--
ALTER TABLE `articles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `classes`
--
ALTER TABLE `classes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=64;

--
-- AUTO_INCREMENT pour la table `eleves`
--
ALTER TABLE `eleves`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `frais_etat`
--
ALTER TABLE `frais_etat`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT pour la table `paiements`
--
ALTER TABLE `paiements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT pour la table `sections`
--
ALTER TABLE `sections`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT pour la table `tarifs`
--
ALTER TABLE `tarifs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=175;

--
-- AUTO_INCREMENT pour la table `utilisateurs`
--
ALTER TABLE `utilisateurs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
