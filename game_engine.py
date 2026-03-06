"""
=============================================================
 PÉDANTIX CLONE — Moteur de Jeu
=============================================================
 Reproduit le fonctionnement de Pédantix :
 - Récupère une page Wikipédia (intro uniquement)
 - Masque tous les mots
 - Le joueur propose des mots successifs
 - Les mots exacts sont révélés en blanc
 - Les mots proches sémantiquement sont grisés (par niveau)
 - Victoire quand tous les mots du TITRE sont trouvés
=============================================================
"""

import re
import unicodedata
import json
import os
import random
import hashlib
from datetime import datetime
from difflib import SequenceMatcher


# ─────────────────────────────────────────────
#  LISTE DE PAGES WIKIPEDIA POUR LE JEU
#  (On simule la sélection quotidienne + aléatoire)
# ─────────────────────────────────────────────

CAMPAIGN_PAGES = [
    "La Reunion", "Laser", "Blaise Pascal", "Kilimandjaro", "Christophe Colomb",
    "Martin Luther King", "Frida Kahlo", "Gravitation universelle", "Les Simpson", "Opera",
    "Victor Hugo", "Stoicisme", "Golf", "Cellule (biologie)", "Michael Schumacher",
    "Beethoven", "Rayons X", "Grece antique", "Tableau periodique des elements", "Premiere Guerre mondiale",
    "Conscience", "Bach", "Attentats du 11 septembre 2001", "Circuit integre", "Moliere",
    "Zinedine Zidane", "Lion", "Erosion", "Dordogne", "Liaison chimique",
    "Requin blanc", "Mississippi", "Pulsar", "La Fayette", "Empire britannique",
    "Napoleon III", "Francis Bacon", "Echecs", "Seisme", "Sahara",
    "Atmosphere terrestre", "Meiose", "Arctique", "Istanbul", "Monnaie",
    "Lorraine", "Gange", "Hip-hop", "Peninsule arabique", "New York",
    "Francisco Pizarro", "Socrate", "Utilitarisme", "Romantisme", "Jules Cesar",
    "Vienne", "Suffrage universel", "Pyrenees", "Mont Blanc", "Intelligence artificielle",
    "Rio de Janeiro", "Bombe atomique", "Formule 1", "Nil", "Charles de Gaulle",
    "Laicite", "Art baroque", "Rome", "Pile a hydrogene", "Natation",
    "Platon", "Muhammad Ali", "Totalitarisme", "Architecture romane", "Serena Williams",
    "Bouddhisme", "Scandinavie", "Ballet", "Radioactivite", "Rhone",
    "Jean-Paul Sartre", "Liège", "Verite", "Baleine bleue", "Ecriture",
    "Daenerys Targaryen", "Musee du Louvre", "Copernic", "Everest", "Clovis Ier",
    "Mao Zedong", "Sydney", "Renaissance", "Thermodynamique", "Mexico",
    "Aristote", "Paris", "Neoplatonisme", "Realite virtuelle", "Will Smith"
    #"Imagerie par resonance magnetique", "Train a grande vitesse", "Reptile", "Telephone", "Ibn Battuta",
    #"Jazz", "Londres", "Nanotechnologie", "Antarctique", "Raphael",
    #"Danton", "OGM", "Churchill", "Nantes", "Galerie des Offices",
    #"Coupe Davis", "Gottfried Wilhelm Leibniz", "Mont Fuji", "Marguerite de Navarre", "Papillon",
    #"Voltaire", "Revolution chinoise", "Jeux olympiques d'ete", "Biosphere", "Peste noire",
    #"Ethique", "Absolutisme monarchique", "Amsterdam", "Massif central", "Blues",
    #"Schubert", "Charlemagne", "Francois Ier", "Ligue des champions de l'UEFA", "Reforme protestante",
    #"Thomas Jefferson", "Guerre froide", "Marcel Duchamp", "Machine a vapeur", "Bernard Hinault",
    #"Guadeloupe", "Veda", "Lenine", "Jerusalem", "Vosges",
    #"Guyane", "Islam", "Traite de Versailles", "Guerre du Viet Nam", "Rafael Nadal",
    #"Electromagnetisme", "Pont du Gard", "Nicolas Machiavel", "Empire byzantin", "Bauhaus",
    #"Roger Federer", "Henri Matisse", "Henri IV", "Talmud", "Marie-Antoinette",
    #"Alpes", "Amphibien", "Abolition de l'esclavage", "Dissolution de l'URSS", "Poesie",
    #"Impressionnisme", "Etretat", "Big Bang", "Plastique", "Boussole",
    #"Grande Barriere de Corail", "Evolution", "Scepticisme", "Marcel Proust", "Leonardo da Vinci",
    #"George Washington", "Guerre du Golfe", "Marat", "Clonage", "Pele",
    #"Egypte antique", "Le Caire", "Reaction nucleaire", "Rugby a XV", "Emmanuel Kant",
    #"Staline", "Euclide", "Giordano Bruno", "Pythagore", "Florence",
    #"Architecture gothique", "Guerre en Afghanistan", "Paul Cezanne", "Tour de France", "Alsace",
    #"Fourmi", "Tocqueville", "Darwin", "Patagonie", "Friedrich Nietzsche",
    #"Revolution russe", "Decolonisation", "Fibre optique", "Tiger Woods", "Volcan",
    #"Chris Froome", "Chateau de Chambord", "Louis XVI", "Proteine", "Sacre-Coeur de Montmartre",
    #"Satellite artificiel", "Beton arme", "Structuralisme", "Colonialisme", "Michael Jordan",
    #"Blockchain", "Abeille", "Coran", "Humanisme", "Philippe II de France",
    #"Systeme solaire", "Usain Bolt", "Vasco de Gama", "Automobile", "Toulouse",
    #"Hitler", "Vercingetorix", "Pablo Picasso", "Ocean Indien", "Football",
    #"Cricket", "Atheisme", "Voie lactee", "Epicurisme", "Bordeaux",
    #"Centrale nucleaire", "Kepler", "Cyclisme", "Mer Mediterranee", "Insecte",
    #"Metaphysique", "Andre-Marie Ampere", "Nice", "Mecanique quantique", "Dauphin",
    #"Photosynthese", "Newton", "Lazare Carnot", "Lac d'Annecy", "Gorges du Verdon",
    #"Tectonique des plaques", "Georg Wilhelm Friedrich Hegel", "Nintendo", "Jesse Owens", "Tennis",
    #"Rennes", "Esclavage", "Liberte", "Camargue", "Revolution americaine",
    #"Mer des Caraibes", "Telescope spatial", "Madame de Pompadour", "Guerre d'Espagne", "Catherine de Medicis",
    #"Philosophie", "Diego Maradona", "Radio", "Accelerateur de particules", "Louis Pasteur",
    #"Pekin", "Art nouveau", "Musee du Louvre", "Fusee", "Einstein",
    #"Effet de serre", "Revolution industrielle", "Supernova", "Botticelli", "Internet",
    #"Vesuve", "Lyon", "Rembrandt", "Energie solaire", "Architecture Renaissance",
    #"Bande dessinee", "Penicilline", "Marco Polo", "Organisation des Nations unies", "Araignee",
    #"Marx", "Freud", "Genocide armenien", "Arthur Schopenhauer", "Elephant",
    #"Auguste Comte", "Cynisme", "Smartphone", "Provence", "Henri II de France",
    #"Bretagne", "Aconcagua", "Television", "Charlie Chaplin", "Rene Descartes",
    #"Revolution francaise", "Atlantique", "Vincent van Gogh", "Napoleon Bonaparte", "Shoah",
    #"Empire mongol", "Garibaldi", "Galapagos", "Musee du Prado", "Basket-ball",
    #"Poudre a canon", "Paul Gauguin", "Himalaya", "Magellan", "Perse antique",
    #"Tycho Brahe", "Yangzi Jiang", "Montesquieu", "Louis XIV", "Wimbledon",
    #"Bismarck", "Exoplanete", "Denis Diderot", "Valentino Rossi", "Coupe du monde de football",
    #"Nouvelle Vague", "Logique", "Existentialisme", "Mozart", "Marie Curie",
    #"Union europeenne", "Garonne", "Apartheid", "Poisson", "Christianisme",
    #"Venise", "Barcelone", "Anne de Bretagne", "Claude Monet", "Coupe du monde de rugby",
    #"Roland-Garros", "Jean-Jacques Rousseau", "Ho Chi Minh", "Michel-Ange", "Colbert",
    #"Pierre de Fermat", "Seconde Guerre mondiale", "Croisades", "Roosevelt", "Acier",
    #"Baruch Spinoza", "Trou noir", "Droits de l'homme", "Enzyme", "Declaration universelle des droits de l'homme",
    #"Jura", "Empire ottoman", "Baseball", "Loire", "Carl Lewis",
    #"Justice", "Mandela", "Ecosysteme", "Hollywood", "ADN",
    #"Empire romain", "Roman (litterature)", "GPS", "Microscope", "Transplantation cardiaque",
    #"Feodalite", "Montpellier", "Diane de Poitiers", "Languedoc", "Relativite restreinte",
    #"Amazone", "Go (jeu)", "Arc de triomphe de l'Etoile", "Saint Louis", "Pacifique",
    #"Imprimerie", "Judaisme", "Chute du mur de Berlin", "Electricite", "Ayrton Senna",
    #"Champagne-Ardenne", "Lionel Messi", "Mammifere", "Hindouisme", "Lance Armstrong",
    #"Postmodernisme", "Genocide au Rwanda", "Hernan Cortes", "Agnosticisme", "Vermeer",
    #"Fouche", "Alfred Hitchcock", "Musee de l'Ermitage", "Eddy Merckx", "Bourgogne",
    #"Art deco", "Strasbourg", "Buenos Aires", "Peninsule iberique", "Simon Bolivar",
    #"Siberie", "Rock and roll", "Cycle de l'eau", "Athletisme", "Torah",
    #"Alexandre le Grand", "Ayrton Senna", "Libre arbitre", "Baie du Mont-Saint-Michel", "Roue",
    #"Cathedrale Notre-Dame de Paris", "Manga", "Mazarin", "Talleyrand", "Avion",
    #"Archimede", "Traite negriere", "Sahel", "Wassily Kandinsky", "Chopin",
    #"Martin Heidegger", "Amazonie", "OTAN", "Saint-Just", "Desert de Gobi",
    #"Galilee", "Guerre de Coree", "Dinosaure", "Eolienne", "Richelieu",
    #"Mysticisme", "Normandie", "Auguste Renoir", "Athenes", "Thomas More",
    #"Lagos", "Antoine Lavoisier", "Desert du Kalahari", "Lewis Hamilton", "Nadia Comaneci",
    #"Tokyo", "Genome humain", "Tour Eiffel", "Che Guevara", "Cristiano Ronaldo",
    #"Mumbai", "Jeux video", "Ordinateur", "Cavour", "Roger Bacon",
    #"Semi-conducteur", "Jeanne d Arc", "Bible", "Animisme", "Martinique",
    #"Surrealisme", "Glaciation", "Mont-Saint-Michel", "Fusion nucleaire", "Jeux olympiques d'hiver",
    #"Robotique", "Theatre grec antique", "Vaccin", "Marseille", "Printemps arabe",
    #"Albert Camus", "Salvador Dali", "Mesopotamie", "Musee d'Orsay", "Versailles",
    #"Joseph Fourier", "Gustave Eiffel", "Robespierre", "Mitose", "Cubisme",
    #"Henri Bergson", "Empire colonial francais", "Jeux olympiques", "Novak Djokovic", "Museum of Modern Art",
    #"Cleopatre", "Wi-Fi", "Gandhi", "Carcassonne", "Seine",
    #"Corse", "Reseau social", "Simone de Beauvoir", "Shakespeare", "Musique classique",
]

DAILY_PAGES = [
        # Litterature mondiale
    "Don Quichotte", "Hamlet", "Faust (Goethe)", "L'Odyssee", "L'Iliade",
    "La Divine Comedie", "Guerre et Paix", "Crime et Chatiment", "Anna Karenine", "Les Miserables",
    #"Notre-Dame de Paris (roman)", "Le Rouge et le Noir", "Madame Bovary", "La Recherche du temps perdu", "L'Etranger (Camus)",
    #"Le Petit Prince", "Candide (Voltaire)", "Les Fleurs du mal", "Arthur Rimbaud", "Paul Verlaine",
    #"Honore de Balzac", "Stendhal", "Gustave Flaubert", "Emile Zola", "Guy de Maupassant",
    #"Jules Verne", "Alexandre Dumas", "George Sand", "Alphonse de Lamartine", "Alfred de Musset",
    #"Franz Kafka", "James Joyce", "Samuel Beckett", "Fiodor Dostoievski", "Leon Tolstoi",
    #"Nicolas Gogol", "Anton Tchekhov", "Ivan Tourgueniev", "Miguel de Cervantes", "Johann Wolfgang von Goethe",
    #"William Blake", "John Milton", "Geoffrey Chaucer", "Dante Alighieri", "Francois Rabelais",
    #"Montaigne", "Jean de La Fontaine", "Pierre Corneille", "Jean Racine", "Charles Baudelaire",
        # Musique
    "Ludwig van Beethoven", "Johann Sebastian Bach", "Frederic Chopin", "Franz Schubert", "Johannes Brahms",
    "Richard Wagner", "Giuseppe Verdi", "Giacomo Puccini", "Claude Debussy", "Igor Stravinski",
    #"Dmitri Chostakovitch", "Sergue Rachmaninov", "Piotr Ilitch Tchaiokvski", "George Gershwin", "Duke Ellington",
    #"Miles Davis", "John Coltrane", "Louis Armstrong", "Elvis Presley", "The Beatles",
    #"Bob Dylan", "Jimi Hendrix", "David Bowie", "Michael Jackson", "Madonna",
    #"Prince (musicien)", "Bob Marley", "Edith Piaf", "Johnny Hallyday", "Jacques Brel",
    #"Georges Brassens", "Serge Gainsbourg", "Symphonie numero 9 de Beethoven", "La Flute enchantee", "Carmen (opera)",
    #"La Traviata", "Le Sacre du printemps", "Bolero de Ravel", "Requiem de Mozart", "Les Quatre Saisons",
    #"Opera Garnier", "Philharmonie de Berlin", "Festival de Bayreuth", "Franz Liszt", "Hector Berlioz",
    #"Camille Saint-Saens", "Gabriel Faure", "Erik Satie", "Maurice Ravel", "Darius Milhaud",
        # Cinema
    "Citizen Kane", "Hunger Games (serie de films)", "Twilight", "Les Temps modernes", "Le Dictateur",
    "Psychose (film)", "Inception", "Le Parrain", "Festival de Cannes", "Taxi Driver",
    #"2001 L'Odyssee de l'espace", "Blade Runner", "Star Wars", "Indiana Jones", "E.T.",
    #"Matrix", "Sueurs froides", "Titanic (film)", "Avatar (film)", "Jurassic Park",
    #"Amarcord", "Huit et demi", "La Dolce Vita", "La Regle du jeu", "Les Enfants du paradis",
    #"A bout de souffle", "Le Mepris", "Akira Kurosawa", "Ingmar Bergman", "Federico Fellini",
    #"Jean-Luc Godard", "Francois Truffaut", "Stanley Kubrick", "Orson Welles", "John Ford",
    #"Freres Lumiere", "Georges Melies", "Cinema muet", "Technicolor", "Effets speciaux",
    #"Apocalypse Now", "Oscar du cinema", "Cesar du cinema", "Mostra de Venise", "Berlinale",
    #"Walt Disney", "Animation japonaise", "Studio Ghibli", "Hayao Miyazaki", "Buster Keaton",
        # Sciences humaines
    "Anthropologie", "Sociologie", "Psychologie", "Sciences economiques", "Linguistique",
    "Archeologie", "Prehistoire", "Paleontologie", "Geologie", "Climatologie",
    #"Carl Gustav Jung", "Jacques Lacan", "Jean Piaget", "Ivan Pavlov", "Behaviorisme",
    #"Max Weber", "Emile Durkheim", "Pierre Bourdieu", "Claude Levi-Strauss", "Michel Foucault",
    #"Adam Smith", "David Ricardo", "John Maynard Keynes", "Friedrich Hayek", "Milton Friedman",
    #"Ferdinand de Saussure", "Noam Chomsky", "Roland Barthes", "Jacques Derrida", "Louis Althusser",
    #"Feminisme", "Suffragettes", "Olympe de Gouges", "Simone Veil", "Gloria Steinem",
    #"Demographie", "Urbanisme", "Geopolitique", "Mondialisation", "Migration",
    #"Colonisation", "Neocolonialisme", "Tiers-monde", "Developpement durable", "Economie mondiale",
    #"Crise economique de 1929", "Stagflation", "Neoliberalisme", "Keynesianisme", "Mondialisation economique",
        # Biologie et medecine
    "Cancer", "Panda geant", "Coronavirus", "Hippocrate", "Radiotherapie",
    "Paludisme", "Tuberculose", "Heredite", "Chimpanze", "Alexander Fleming",
    #"Coeur", "Cerveau humain", "Poumon", "Foie", "Rein",
    #"Systeme nerveux", "Systeme immunitaire", "Systeme digestif", "Systeme endocrinien", "Systeme cardiovasculaire",
    #"Genetique", "Chromosome", "Gene", "Mutation genetique", "Cholera",
    #"Gregor Mendel", "Francis Crick", "Louis Pasteur (microbiologie)", "Robert Koch", "Poliomyelite",
    #"Chirurgie", "Anesthesie", "Antibiotherapie", "Chimiotherapie", "Lepre",
    #"Grippe espagnole", "Galien", "Avicenne", "Andreas Vesale", "William Harvey",
    #"Neurosciences", "Psychologie cognitive", "Ethologie", "Primatologie", "Jane Goodall",
    #"Tigre", "Gorille", "Variole", "Syndrome d'immunodeficience acquise", "Rhinoceros blanc",
        # Mythologie et religion
    "Mythologie grecque", "Mythologie romaine", "Catholicisme", "Islam sunnite", "Confucius",
    "Zeus", "Athena", "Toutankhamon", "Hermes", "Poseidon",
    #"Heracles", "Achille", "Ulysse", "Orphee", "Promethee",
    #"Odin", "Thor", "Loki", "Freya", "Valhalla",
    #"Ramses II", "Apollon", "Isis", "Osiris", "Horus",
    #"Jesus de Nazareth", "Mahomet", "Gautama Bouddha", "Mythologie mesopotamienne", "Zoroastre",
    #"Mythologie nordique", "Protestantisme", "Orthodoxie orientale", "Mythologie egyptienne", "Islam chiite",
    #"Vatican", "La Mecque", "Jerusalem (ville sainte)", "Varanasi", "Lhassa",
    #"Inquisition", "Concile de Trente", "Guerres de Religion", "Martin Luther", "Jean Calvin",
    #"Taoisme", "Shintoisme", "Sikhisme", "Chamanisme", "Jaïnisme",
        # Architecture et patrimoine
    "Parthenon", "Colisee de Rome", "Pyramides de Gizeh", "Angkor Vat", "Machu Picchu",
    "Taj Mahal", "Grande Muraille de Chine", "Alhambra", "Sagrada Familia", "Burj Khalifa",
    #"Stonehenge", "Petra (Jordanie)", "Chichen Itza", "Pompei", "Persepolis",
    #"Cathedrale de Chartres", "Cathedrale de Reims", "Cathedrale de Cologne", "Cathedrale de Seville", "Basilique Saint-Pierre",
    #"Chateau de Windsor", "Palais de Buckingham", "Kremlin de Moscou", "Cite interdite", "Palais imperial de Tokyo",
    #"Acropole d'Athenes", "Forum romain", "Pantheon de Rome", "Arc de Titus", "Tour de Londres",
    #"Opera de Sydney", "Empire State Building", "Chrysler Building", "One World Trade Center", "Centre Pompidou",
    #"Palazzo Vecchio", "Pont du Rialto", "Basilique Saint-Marc", "Duomo de Florence", "Baptistere de Florence",
    #"Chateau de Neuschwanstein", "Palais de Schonbrunn", "Palais de Sans-Souci", "Palais royal de Madrid", "Palais de Topkapi",
    #"Abbaye de Cluny", "Le Corbusier", "Frank Lloyd Wright", "Renzo Piano", "Zaha Hadid",
        # Politique et droit
    "Republique francaise", "Monarchie constitutionnelle", "Droit penalRegime presidentiel", "Regime parlementaire", "Federalisme",
    "Constitution francaise", "Parlement europeen", "UNESCO", "Cour internationale de justice", "Banque mondiale",
    #"Declaration des droits de l'homme et du citoyen", "Constitution des Etats-Unis", "Magna Carta", "Declaration d'independance des Etats-Unis", "Charte des Nations unies",
    #"Habeas corpus", "Presomption d'innocence", "Droit international humanitaire", "Regime presidentiel", "Droit civil",
    #"Fonds monetaire international", "Cour penale internationale", "Organisation mondiale du commerce", "G7", "G20",
    #"BRICS", "ASEAN", "Union africaine", "Mercosur", "Ligue arabe",
    #"Communisme", "Socialisme democratique", "Liberalisme politique", "Conservatisme", "Fascisme",
    #"Nationalisme", "Anarchisme", "Social-democratie", "Populisme", "Souverainisme",
    #"Plan Marshall", "Detente (guerre froide)", "Glasnost", "Perestroika", "Solidarnosc",
    #"Conseil de securite de l'ONU", "Organisation mondiale de la sante", "UNICEF", "UNHCR", "Programme alimentaire mondial",
        # Gastronomie et culture
    "Gastronomie francaise", "Cuisine italienne", "Cuisine japonaise", "Mardi Gras", "Louis Vuitton",
    "Jeu de go", "Champagne (boisson)", "Mahjong", "Paella", "Biere",
    #"Fromage", "Baguette (pain)", "Croissant", "Foie gras", "Truffe (gastronomie)",
    #"Sushi", "Ramen", "Pizza", "Pasta", "Whisky",
    #"Haute couture", "Chanel", "Christian Dior", "Cuisine indienne", "Hermes (marque)",
    #"Parfum", "Cartier (joaillerie)", "Yves Saint Laurent", "Givenchy", "Balenciaga",
    #"Tintin", "Asterix", "Lucky Luke", "Les Schtroumpfs", "Blake et Mortimer",
    #"Jeux olympiques antiques", "Carnaval de Venise", "Oktoberfest", "Cuisine chinoise", "Fete nationale francaise",
    #"Cirque", "Commedia dell'arte", "Pantomime", "Cuisine japonaise", "Music-hall",
    #"Jeu d'echecs (histoire)", "Vin de Bordeaux", "Poker", "Bridge (jeu)", "Cognac (eau-de-vie)",
        # Exploration et espace
    "Exploration spatiale", "Lune", "Mars (planete)", "Station spatiale internationale", "Pole Nord",
    "Neil Armstrong", "Youri Gagarine", "Naufrage du Titanic", "Everest (alpinisme)", "Montgolfiere",
    #"Mission Apollo 11", "Spoutnik 1", "Navette spatiale", "Fusee Saturn V", "SpaceX",
    #"Ernest Shackleton", "Roald Amundsen", "Robert Falcon Scott", "Edmund Hillary", "Tenzing Norgay",
    #"Expedition Lewis et Clark", "David Livingstone", "Henry Morton Stanley", "Richard Francis Burton", "John Hanning Speke",
    #"Sous-marin", "Jacques-Yves Cousteau", "Valentina Terechkova", "Abysses", "Fond oceanique",
    #"John Glenn", "Charles Lindbergh", "Amelia Earhart", "Freres Wright", "Louis Bleriot",
    #"Vingt mille lieues sous les mers", "De la Terre a la Lune", "Voyage au centre de la Terre", "L'Ile mysterieuse", "Michel Strogoff",
    #"Howard Carter", "Tombeau de Toutankhamon", "Troie (site archeologique)", "Pompei (fouilles)", "Machu Picchu (decouverte)",
    #"Telescope spatial Hubble", "Pole Sud", "Buzz Aldrin", "K2", "Pole magnetique",
]

# Backward compat
WIKIPEDIA_PAGES = CAMPAIGN_PAGES



# ─────────────────────────────────────────────
#  UTILITAIRES TEXTE
# ─────────────────────────────────────────────

def normalize(word: str) -> str:
    """Normalise un mot : minuscule, sans accents, sans ponctuation."""
    word = word.lower().strip()
    # Supprimer les accents
    word = ''.join(
        c for c in unicodedata.normalize('NFD', word)
        if unicodedata.category(c) != 'Mn'
    )
    # Garder uniquement les lettres et chiffres
    word = re.sub(r"[^a-z0-9]", "", word)
    return word


def stem_word(word: str) -> str:
    """Stemming simple français : retire suffixes courants."""
    w = normalize(word)
    suffixes = ['ement', 'ation', 'itions', 'ition', 'ments', 'ment',
                'aient', 'aient', 'euse', 'eux', 'aux', 'aux',
                'ique', 'iques', 'iste', 'istes', 'iser', 'ise',
                'elles', 'elle', 'els', 'el', 'aux', 'al',
                'ants', 'ant', 'ente', 'ents', 'ent',
                'ées', 'ée', 'és', 'é',
                'ons', 'ions', 'ez', 'er', 'ir',
                'ux', 'ux', 's']
    for suffix in suffixes:
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            return w[:-len(suffix)]
    return w


def similarity_score(word1: str, word2: str) -> float:
    """
    Calcule un score de proximité entre deux mots.
    Utilise plusieurs heuristiques pour simuler Word2Vec :
    - Correspondance exacte → 1.0
    - Même radical (stem) → 0.85
    - Correspondance partielle (SequenceMatcher) → valeur proportionnelle
    - Sinon → 0.0
    """
    n1 = normalize(word1)
    n2 = normalize(word2)

    if not n1 or not n2:
        return 0.0

    # Exact match
    if n1 == n2:
        return 1.0

    # Même radical
    if stem_word(n1) == stem_word(n2) and len(stem_word(n1)) >= 3:
        return 0.85

    # Préfixe commun long
    min_len = min(len(n1), len(n2))
    if min_len >= 4:
        common_prefix = 0
        for a, b in zip(n1, n2):
            if a == b:
                common_prefix += 1
            else:
                break
        if common_prefix >= min_len * 0.75:
            return 0.70

    # SequenceMatcher pour similarité de chaîne
    ratio = SequenceMatcher(None, n1, n2).ratio()
    if ratio >= 0.80:
        return round(ratio * 0.65, 2)

    return 0.0


def proximity_level(score: float) -> str:
    """
    Retourne le niveau de proximité visuel.
    'exact'  → le mot est dans le texte
    'proche' → très proche (gris foncé)
    'tiede'  → proche (gris moyen)
    'froid'  → peu proche (gris clair)
    'rien'   → aucun rapport
    """
    if score >= 1.0:
        return 'exact'
    elif score >= 0.80:
        return 'proche'
    elif score >= 0.65:
        return 'tiede'
    elif score >= 0.50:
        return 'froid'
    else:
        return 'rien'


# ─────────────────────────────────────────────
#  RÉCUPÉRATION WIKIPEDIA
# ─────────────────────────────────────────────

def get_wikipedia_intro(title: str) -> tuple[str, str]:
    """
    Récupère 3 à 4 paragraphes depuis une page Wikipédia.
    Sans exintro : récupère le corps complet, puis on garde
    les N premiers paragraphes non vides jusqu'à ~500 mots.
    """
    try:
        import urllib.request
        import urllib.parse

        params = urllib.parse.urlencode({
            'action': 'query',
            'titles': title,
            'prop': 'extracts',
            # PAS de exintro : on veut tout le corps de l'article
            'explaintext': True,
            'exsectionformat': 'plain',  # pas de titres de sections
            'redirects': True,
            'format': 'json',
            'utf8': True,
        })
        url = f"https://fr.wikipedia.org/w/api.php?{params}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'PedantixClone/1.0 (educational game)'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if page_id == '-1':
                break
            real_title = page_data.get('title', title)
            full_text = page_data.get('extract', '').strip()
            if not full_text or len(full_text) < 50:
                break

            # Découper en paragraphes (séparés par lignes vides ou \n)
            paragraphs = [p.strip() for p in re.split(r'\n{2,}', full_text) if p.strip()]

            # Filtrer les paragraphes trop courts (titres de sections, notes)
            # et ceux qui ressemblent à des titres (pas de point, courts)
            good = []
            for p in paragraphs:
                # Ignorer les pseudo-titres de section (courts, sans ponctuation de fin)
                if len(p) < 80 and not re.search(r'[.!?]', p):
                    continue
                good.append(p)

            # Prendre les paragraphes jusqu'à atteindre ~400-600 mots
            selected = []
            total_words = 0
            for p in good:
                words_in_p = len(p.split())
                selected.append(p)
                total_words += words_in_p
                # S'arrêter après 4 paragraphes ou ~600 mots
                if len(selected) >= 4 or total_words >= 600:
                    break

            # Si on n'a rien de bon, prendre les 600 premiers mots bruts
            if not selected:
                words = full_text.split()
                return real_title, ' '.join(words[:600]) + '…'

            extract = '\n\n'.join(selected)
            return real_title, extract

    except Exception:
        pass

    # ── Fallback : API summary ──
    try:
        import urllib.request
        import urllib.parse
        encoded = urllib.parse.quote(title.replace(' ', '_'))
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'PedantixClone/1.0 (educational game)'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get('title', title), data.get('extract', '')
    except Exception:
        pass

    # ── Fallback final ──
    return title, (
        f"{title} est un sujet important dans l'histoire et la culture mondiale. "
        f"Il est reconnu pour ses nombreuses contributions et son influence considérable. "
        f"Son histoire est riche et complexe, marquée par des événements déterminants "
        f"qui ont façonné le monde tel que nous le connaissons aujourd'hui. "
        f"De nombreux chercheurs et historiens se sont penchés sur ce sujet fascinant."
    )


# ─────────────────────────────────────────────
#  TOKENISATION DU TEXTE
# ─────────────────────────────────────────────

def tokenize_text(text: str) -> list[dict]:
    """
    Découpe le texte en tokens : mots et non-mots.
    Les tirets et apostrophes sont toujours visibles (ponctuation normale).
    Chaque partie d'un mot composé ou élidé est un mot indépendant.
    Ex : "l'accusé"   → [l] ['] [accusé]
         "sous-estime" → [sous] [-] [estime]
    """
    tokens = []
    # Séparer sur tout ce qui n'est pas une lettre/chiffre
    # (tirets, apostrophes, espaces, virgules, etc.)
    pattern = re.compile(r"([a-zA-ZÀ-ÿ0-9]+|[^a-zA-ZÀ-ÿ0-9]+)")

    for match in pattern.finditer(text):
        chunk = match.group()
        if re.match(r"^[a-zA-ZÀ-ÿ0-9]", chunk):
            # Mot normal
            tokens.append({
                'type': 'word',
                'text': chunk,
                'normalized': normalize(chunk),
                'revealed': False,
                'proximity': 'rien',
                'best_score': 0.0,
            })
        else:
            # Toute ponctuation est visible dès le début
            tokens.append({
                'type': 'punct',
                'text': chunk,
                'revealed': True,
                'proximity': 'exact',
            })
    return tokens


# ─────────────────────────────────────────────
#  CLASSE PRINCIPALE : PARTIE
# ─────────────────────────────────────────────

class PedantixGame:
    """
    Représente une partie de Pédantix.
    
    Utilisation :
        game = PedantixGame()
        game.start("Tour Eiffel")
        result = game.guess("construction")
        # result = {'matches': 3, 'proximity_hits': [...], 'won': False}
    """

    def __init__(self):
        self.title = ""
        self.title_words = []          # mots normalisés du titre
        self.intro_text = ""
        self.tokens = []               # liste de tokens (voir tokenize_text)
        self.guesses = []              # historique des propositions
        self.guess_count = 0
        self.won = False
        self.started = False
        self.start_time = None

    def start(self, page_title: str) -> bool:
        """Initialise la partie avec une page Wikipedia."""
        real_title, intro = get_wikipedia_intro(page_title)

        self.title = real_title
        self.intro_text = intro
        self.tokens = tokenize_text(intro)

        # Mots du titre (normalisés)
        self.title_words = [
            normalize(w)
            for w in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", real_title)
            if len(normalize(w)) >= 2
        ]

        # Tracker quels mots du titre ont été trouvés
        self.title_found = {w: False for w in self.title_words}

        self.guesses = []
        self.guess_count = 0
        self.won = False
        self.started = True
        self.start_time = datetime.now()
        return True

    def guess(self, word: str) -> dict:
        """
        Traite une proposition du joueur.
        
        Retourne un dict :
        {
            'word': str,                  # le mot proposé
            'matches': int,               # nb de mots révélés (exact)
            'proximity_results': [        # détail par token mis à jour
                {'text': str, 'proximity': str, 'score': float}
            ],
            'already_guessed': bool,
            'won': bool,
            'title_progress': int,        # % du titre découvert
        }
        """
        if not self.started:
            return {'error': 'Partie non démarrée'}

        word = word.strip()
        if not word:
            return {'error': 'Mot vide'}

        norm_guess = normalize(word)

        # Déjà proposé ?
        already = norm_guess in [normalize(g['word']) for g in self.guesses]

        matches = 0
        proximity_results = []

        for token in self.tokens:
            if token['type'] != 'word':
                continue

            score = similarity_score(word, token['text'])
            level = proximity_level(score)

            if score > token.get('best_score', 0.0):
                token['best_score'] = score
                token['proximity'] = level
                # Mémoriser le mot proposé (pour l'affichage orange)
                if level != 'exact':
                    token['best_word'] = word
                else:
                    token.pop('best_word', None)

                if level == 'exact':
                    token['revealed'] = True
                    matches += 1
                    # Vérifier si c'est un mot du titre
                    if token['normalized'] in self.title_found:
                        self.title_found[token['normalized']] = True

            if level != 'rien':
                proximity_results.append({
                    'text': token['text'],
                    'proximity': level,
                    'score': round(score, 2),
                })

        self.guess_count += 1
        self.guesses.append({
            'word': word,
            'matches': matches,
            'count': self.guess_count,
        })

        # Vérifier la victoire
        self.won = all(self.title_found.values()) and len(self.title_words) > 0

        # Progression du titre
        found_title = sum(1 for v in self.title_found.values() if v)
        title_progress = int(found_title / max(len(self.title_words), 1) * 100)

        return {
            'word': word,
            'matches': matches,
            'proximity_results': proximity_results,
            'already_guessed': already,
            'won': self.won,
            'title_progress': title_progress,
            'guess_count': self.guess_count,
        }

    def get_display_tokens(self) -> list[dict]:
        """
        Retourne les tokens pour l'affichage :
        - mots révélés → texte visible
        - mots non révélés → blocs gris (longueur visible, niveau de gris)
        """
        display = []
        for token in self.tokens:
            if token['type'] == 'punct':
                display.append({'type': 'punct', 'text': token['text']})
            elif token['type'] == 'hidden_punct':
                # Tiret masqué : visible seulement quand les mots adjacents sont révélés
                display.append({
                    'type': 'hidden_punct',
                    'text': token['text'],
                    'revealed': token.get('revealed', False),
                    'proximity': token.get('proximity', 'rien'),
                    'length': 1,
                })
            elif token['revealed']:
                display.append({
                    'type': 'word',
                    'text': token['text'],
                    'revealed': True,
                    'proximity': 'exact',
                })
            else:
                display.append({
                    'type': 'word',
                    'text': None,
                    'length': len(token['text']),
                    'revealed': False,
                    'proximity': token['proximity'],
                    'best_word': token.get('best_word', None),
                })
        return display

    def get_title_display(self) -> list[dict]:
        """Retourne les mots du titre (révélés ou masqués)."""
        title_tokens = []
        for match in re.finditer(r"[a-zA-ZÀ-ÿ0-9]+|[^a-zA-ZÀ-ÿ0-9]+", self.title):
            chunk = match.group()
            if re.match(r"^[a-zA-ZÀ-ÿ0-9]", chunk):
                norm = normalize(chunk)
                found = self.title_found.get(norm, False) if hasattr(self, 'title_found') else False
                title_tokens.append({
                    'type': 'word',
                    'text': chunk,
                    'revealed': found,
                    'length': len(chunk),
                })
            else:
                title_tokens.append({'type': 'punct', 'text': chunk})
        return title_tokens

    def get_stats(self) -> dict:
        """Retourne les statistiques de la partie."""
        elapsed = (datetime.now() - self.start_time).seconds if self.start_time else 0
        return {
            'guess_count': self.guess_count,
            'elapsed_seconds': elapsed,
            'won': self.won,
            'title': self.title if self.won else '???',
            'words_revealed': sum(1 for t in self.tokens if t['type'] == 'word' and t['revealed']),
            'words_total': sum(1 for t in self.tokens if t['type'] == 'word'),
        }


# ─────────────────────────────────────────────
#  GESTIONNAIRE DE PARTIES
# ─────────────────────────────────────────────

class GameManager:
    """Gere la selection des pages et la progression du joueur."""

    SAVE_FILE = os.path.expanduser("~/.pedantix_saves.json")

    def __init__(self):
        self.data = self._load_data()

    def get_daily_page(self):
        """Retourne (titre, numero_du_jour). Cycle de 500 jours."""
        day = datetime.now().timetuple().tm_yday
        idx = (day - 1) % len(DAILY_PAGES)
        return DAILY_PAGES[idx], day

    def get_campaign_level(self):
        lvl = self.data.get('campaign_level', 1)
        return max(1, min(lvl, len(CAMPAIGN_PAGES)))

    def get_campaign_page(self, level=None):
        if level is None:
            level = self.get_campaign_level()
        level = max(1, min(level, len(CAMPAIGN_PAGES)))
        return CAMPAIGN_PAGES[level - 1], level

    def advance_campaign(self, level):
        completed = self.data.setdefault('campaign_completed', [])
        if level not in completed:
            completed.append(level)
        next_level = level + 1
        while next_level <= len(CAMPAIGN_PAGES) and next_level in completed:
            next_level += 1
        self.data['campaign_level'] = min(next_level, len(CAMPAIGN_PAGES))
        self._save_data()

    def get_campaign_stats(self):
        completed = self.data.get('campaign_completed', [])
        return {
            'current_level': self.get_campaign_level(),
            'completed': len(completed),
            'total': len(CAMPAIGN_PAGES),
            'percent': round(len(completed) / len(CAMPAIGN_PAGES) * 100, 1),
        }

    def start_game(self, mode='daily', level=None, custom_title=None):
        if mode == 'daily':
            page, number = self.get_daily_page()
            meta = {'mode': 'daily', 'day': number}
        elif mode == 'campaign':
            page, number = self.get_campaign_page(level)
            meta = {'mode': 'campaign', 'level': number}
        else:
            page, number = self.get_daily_page()
            meta = {'mode': 'daily', 'day': number}
        game = PedantixGame()
        game.meta = meta
        game.start(page)
        return game

    def save_result(self, game, mode):
        stats = game.get_stats()
        meta = getattr(game, 'meta', {})
        entry = {
            'date': datetime.now().isoformat(),
            'mode': mode,
            'page': game.title,
            'guesses': stats['guess_count'],
            'won': stats['won'],
            'time_seconds': stats['elapsed_seconds'],
            'level': meta.get('level'),
            'day': meta.get('day'),
        }
        self.data.setdefault('history', []).append(entry)
        if mode == 'campaign' and stats['won'] and meta.get('level'):
            self.advance_campaign(meta['level'])
        self._save_data()
        return entry

    def get_history(self):
        return self.data.get('history', [])

    @property
    def history(self):
        return self.data.get('history', [])

    def _load_data(self):
        try:
            if os.path.exists(self.SAVE_FILE):
                with open(self.SAVE_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    if isinstance(d, list):
                        return {'history': d, 'campaign_level': 1, 'campaign_completed': []}
                    return d
        except Exception:
            pass
        return {'history': [], 'campaign_level': 1, 'campaign_completed': []}

    def _save_data(self):
        try:
            with open(self.SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
