import pymysql
import pymysql.cursors
import sys
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session, flash, send_from_directory
from reportlab.lib.pagesizes import letter, A5, A6, landscape, A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import io
import string
from datetime import datetime
import random
import os
from io import BytesIO
from functools import wraps
from flask import make_response
from werkzeug.security import check_password_hash, generate_password_hash
from sms_sender import envoyer_sms
from urllib.parse import unquote
from flask import request, render_template
import bcrypt


def verifier_autorisation(section_cible):
    """
    Vérifie si l'utilisateur connecté a le droit d'accéder à une section donnée.
    - section_cible : 'Maternelle', 'Primaire' ou 'Secondaire'
    - Retourne True si autorisé, False sinon.
    """

    role = session.get('role_utilisateur')

    if not role:
        flash("Utilisateur non connecté.", "danger")
        return False

    if role.lower() == 'full':
        return True  # ✅ Accès total

    if role.lower() == section_cible.lower():
        return True  # ✅ Accès autorisé à sa section

    # ❌ Accès refusé
    flash("⛔ Accès refusé : vous n'êtes pas autorisé à gérer cette section.", "danger")
    return False

#Creation de l'application Flask

app = Flask(__name__)
app.secret_key = 'abc123xyz'  # Clé secrète pour la session

# Chemin absolu vers le dossier de l'application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Dossier pour les reçus
DOSSIER_RECUS = os.path.join(BASE_DIR, "recus")

DOSSIER_STATIC = os.path.join(BASE_DIR,"static")

# Crée le dossier s'il n'existe pas
os.makedirs(DOSSIER_RECUS, exist_ok=True)

def get_db_connection():
    try:
        conn = pymysql.connect(
            host="mervabangi.mysql.pythonanywhere-services.com",
            user="mervabangi",
            password="Gestion2025.",
            database="mervabangi$gestion_eleves_db"
        )

        return conn
    except pymysql.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")
        return None
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('connecte'):
            flash("Vous devez être connecté pour accéder à cette page.", "warning")
            return redirect(url_for('connexion'))
        return f(*args, **kwargs)
    return decorated_function

def log_action(action, nom_utilisateur):
    date_heure = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ligne = f"[{date_heure}] {nom_utilisateur} : {action}\n"
    with open("log.txt", "a", encoding="utf-8") as fichier:
        fichier.write(ligne)

@app.route('/')
def racine():
    return redirect(url_for('connexion'))

#Route pour la page index
@app.route('/accueil')
@login_required
def accueil():
    return render_template('index.html')


from werkzeug.security import check_password_hash

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        nom = request.form['nom']
        mot_de_passe = request.form['mot_de_passe']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom, prenom, mot_de_passe, role
            FROM utilisateurs
            WHERE nom = %s
        """, (nom,))
        utilisateur = cursor.fetchone()
        conn.close()

        if utilisateur and check_password_hash(utilisateur[3], mot_de_passe):
            session['connecte'] = True
            session['user_id'] = utilisateur[0]
            session['nom_utilisateur'] = f"{utilisateur[1]} {utilisateur[2]}"
            session['role_utilisateur'] = utilisateur[4]
            log_action("Connexion réussie", session['nom_utilisateur'])
            return redirect(url_for('accueil'))
        else:
            flash("Identifiants incorrects", "danger")
            return redirect(url_for('connexion'))

    return render_template('connexion.html')


@app.route('/deconnexion')
def deconnexion():
    session.clear()
    
    return redirect(url_for('connexion'))


@app.route("/profil")
@login_required
def profil():
    if not session.get("connecte"):
        return redirect(url_for("connexion"))
    return render_template("profil.html")

import hashlib

@app.route('/changer_mot_de_passe', methods=['GET', 'POST'])
@login_required
def changer_mot_de_passe():
    if 'nom_utilisateur' not in session:
        flash("Veuillez vous connecter d'abord", "danger")
        return redirect(url_for('connexion'))

    nom_utilisateur = session['nom_utilisateur']
    parts = nom_utilisateur.split()
    nom = parts[0]
    prenom = " ".join(parts[1:])  # Gère prénoms composés

    if request.method == 'POST':
        ancien = request.form['ancien']
        nouveau = request.form['nouveau']
        confirmer = request.form['confirmer']

        if nouveau != confirmer:
            flash("Les mots de passe ne correspondent pas", "danger")
            return redirect(url_for('changer_mot_de_passe'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT mot_de_passe FROM utilisateurs 
                WHERE nom = %s AND prenom = %s
            """, (nom, prenom))
            utilisateur = cursor.fetchone()

            if utilisateur and check_password_hash(utilisateur[0], ancien):
                nouveau_hache = generate_password_hash(nouveau, method="pbkdf2:sha256")
                cursor.execute("""
                    UPDATE utilisateurs SET mot_de_passe = %s 
                    WHERE nom = %s AND prenom = %s
                """, (nouveau_hache, nom, prenom))
                conn.commit()

                flash("Mot de passe mis à jour avec succès", "success")
                log_action("Changement de mot de passe", session['nom_utilisateur'])
                return redirect(url_for('menu'))
            else:
                flash("Ancien mot de passe incorrect", "danger")
                log_action("Changement mot de passe échoué", session['nom_utilisateur'])
                return redirect(url_for('changer_mot_de_passe'))

        except mariadb.Error as e:
            flash("Erreur lors de la mise à jour du mot de passe", "danger")
            print(f"Erreur MariaDB : {e}")
            log_action("Erreur SQL - mot de passe", session['nom_utilisateur'])
            return redirect(url_for('changer_mot_de_passe'))

        finally:
            if 'conn' in locals():
                conn.close()

    return render_template('changer_mot_de_passe.html')


#Route Menu
@app.route('/menu')
@login_required
def menu():

    conn = get_db_connection()
    cursor = conn.cursor()
        # Total frais Maternelle
    cursor.execute("""
        SELECT SUM(t.montant)
        FROM eleves e
        JOIN classes c ON e.classe = c.nom
        JOIN tarifs t ON c.id = t.classe_id
        WHERE e.section = 'Maternelle' AND t.type = 'inscription' AND  LOWER(t.statut_eleve) = LOWER(e.statut_eleve)
    """)
    total_frais_maternelle = cursor.fetchone()[0] or 0

    print("Frais maternelle :", total_frais_maternelle)

    # Total frais Primaire
    cursor.execute("""
        SELECT SUM(t.montant)
        FROM eleves e
        JOIN classes c ON e.classe = c.nom
        JOIN tarifs t ON t.classe_id = c.id
        WHERE e.section = 'Primaire' AND t.type = 'inscription' AND LOWER(t.statut_eleve) = LOWER(e.statut_eleve)
    """)
    total_frais_primaire = cursor.fetchone()[0] or 0

    # Total frais Secondaire
    cursor.execute("""
        SELECT SUM(t.montant)
        FROM eleves e
        JOIN classes c ON e.classe = c.nom
        JOIN tarifs t ON t.classe_id = c.id
        WHERE e.section = 'Secondaire' AND t.type = 'inscription' AND LOWER(t.statut_eleve) = LOWER(e.statut_eleve)
    """)
    total_frais_secondaire = cursor.fetchone()[0] or 0

    # Total général frais inscription
    cursor.execute("""
        SELECT SUM(t.montant)
        FROM eleves e
        JOIN classes c ON e.classe = c.nom
        JOIN tarifs t ON t.classe_id = c.id
        WHERE t.type = 'inscription' AND LOWER(t.statut_eleve) = LOWER(e.statut_eleve)
    """)
    total_frais = cursor.fetchone()[0] or 0

    # Nombre total d'élèves
    cursor.execute("SELECT COUNT(*) FROM eleves")
    total_eleves = cursor.fetchone()[0]

    # Nombre de classes différentes
    cursor.execute("SELECT COUNT(DISTINCT classe) FROM eleves")
    total_classes = cursor.fetchone()[0]

    # Nombre de garçons
    cursor.execute("SELECT COUNT(*) FROM eleves WHERE genre = 'Masculin'")
    total_garcons = cursor.fetchone()[0]

    # Nombre de filles
    cursor.execute("SELECT COUNT(*) FROM eleves WHERE genre = 'Féminin'")
    total_filles = cursor.fetchone()[0]

    # Par section
    cursor.execute("SELECT COUNT(*) FROM eleves WHERE section = 'Maternelle'")
    total_maternelle = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM eleves WHERE section = 'Primaire'")
    total_primaire = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM eleves WHERE section = 'Secondaire'")
    total_secondaire = cursor.fetchone()[0]

    conn.close()

    return render_template('menu.html',
        total_frais_maternelle=total_frais_maternelle,
        total_frais_primaire=total_frais_primaire,
        total_frais_secondaire=total_frais_secondaire,
        total_eleves=total_eleves,
        total_classes=total_classes,
        total_frais=total_frais,
        total_garcons=total_garcons,
        total_filles=total_filles,
        total_maternelle=total_maternelle,
        total_primaire=total_primaire,
        total_secondaire=total_secondaire
    )

#Route formulaire d'inscription
@app.route('/inscription', methods=['GET', 'POST'])
@login_required
def inscription():
    role = session.get('role_utilisateur', '')

    if role == 'lecture':
        return redirect(url_for('menu'))  # Ou vers une page où il peut juste consulter

    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Récupération des données du formulaire
            nom = request.form['nom']
            postnom = request.form['postnom']
            prenom = request.form['prenom']
            genre = request.form['genre']
            section = request.form['section']
            # Vérification selon le rôle
            role_utilisateur = session.get('role_utilisateur')

            if role_utilisateur != 'full' and section.lower() != role_utilisateur.lower():
                flash("Vous n’avez pas le droit d’inscrire un élève dans cette section.", "danger")
                return redirect(url_for('inscription'))
            classe = request.form['classe']
            annee_scolaire = request.form['annee_scolaire']
            lieu_naissance = request.form.get('lieu_naissance')
            date_naissance = request.form.get('date_naissance')
            ecole_provenance = request.form.get('ecole_provenance')
            classe_precedente = request.form.get('classe_provenance')
            adresse = request.form.get('adresse')
            responsable = request.form['nom_responsable']
            numero_brut = request.form['telephone']
            if not numero_brut.startswith("+243"):
                telephone_responsable = "+243" + numero_brut
            else:
                telephone_responsable = numero_brut
            fonction_responsable = request.form.get('fonction')
            statut_eleve = request.form.get('statut_eleve')
            frais_inscription = request.form['frais_inscription']
            frais_bulletin = request.form.get('frais_bulletin')
            ram_papier = request.form.get('ram_papier')
            deux_savons = request.form.get('deux_savons')
            deux_ph = request.form.get('deux_ph')
            fournitures = request.form.get('fournitures')

            date_inscription = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


            # 2. Insertion initiale
            cursor.execute("""
                INSERT INTO eleves (
                    nom, postnom, prenom, genre, section, classe,
                    annee_scolaire, date_inscription, lieu_naissance, date_naissance,
                    ecole_provenance, classe_precedente, adresse, responsable, telephone_responsable,
                    fonction_responsable, statut_eleve, frais_inscription, ram_papier,
                    frais_bulletin, deux_savons, deux_ph, fournitures
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nom, postnom, prenom, genre, section, classe,
                annee_scolaire, date_inscription, lieu_naissance, date_naissance,
                ecole_provenance, classe_precedente, adresse, responsable, telephone_responsable,
                fonction_responsable, statut_eleve, frais_inscription, ram_papier,
                frais_bulletin, deux_savons, deux_ph, fournitures
            ))

            log_action("inscription enregistré", session['nom_utilisateur'])

            # 3. Génération du matricule
            eleve_id = cursor.lastrowid
            annee_fin = annee_scolaire.split('-')[1] if '-' in annee_scolaire else annee_scolaire
            matricule = f"{nom[0].upper()}{postnom[0].upper()}{prenom[0].upper()}-{eleve_id}-{annee_fin}"
            cursor.execute("UPDATE eleves SET matricule = %s WHERE id = %s", (matricule, eleve_id))
            print("Matricule généré :", matricule)

            conn.commit()
            # Message de bienvenue
            message = f"C.S.Immaculée Conception de la Charité : Bonjour ! Votre enfant {nom} {postnom} {prenom} a été inscrit avec succès. Merci pour votre confiance."

            # Envoi du SMS dans un bloc sécurisé
            try:
                envoyer_sms(telephone_responsable, message)
            except Exception as sms_error:
                import traceback
                print("Erreur Twilio :", sms_error)
                traceback.print_exc()
                # Tu peux aussi logger dans un fichier ou base si tu as un logger configuré
                log_action(f"Erreur Twilio pour {telephone_responsable}: {sms_error}", session.get('nom_utilisateur', 'Inconnu'))
            conn.close()
            caissier = session.get('nom_utilisateur', 'Inconnu')

            # 4. Génération du reçu PDF
            nom_complet = f"{nom} {postnom} {prenom}"
            filename = f"recu_inscription_{matricule}.pdf"
            filepath = os.path.join(DOSSIER_RECUS, filename)

            c = canvas.Canvas(filepath, pagesize=A6)

            try:
                logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg"))
                logo_droite = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg"))

                    # Logos gauche et droite
                c.drawImage(logo_gauche, 15, 305, width=40, height=40, preserveAspectRatio=True, mask='auto')
                c.drawImage(logo_droite, 245, 305, width=40, height=40, preserveAspectRatio=True, mask='auto')
            except:
                pass
            # Filigrane
            #try:
                    #logo = ImageReader(os.path.join(DOSSIER_STATIC,"logo2.png"))
                    #c.saveState()
                    #c.setFillAlpha(0.08)
                    #c.drawImage(logo, 40, 100, width=240, height=240, preserveAspectRatio=True, mask='auto')
                    #c.restoreState()
            #except:
                    #pass

            # Texte
            c.setFont("Helvetica-Bold", 13)
            c.drawCentredString(149, 320, "COMPLEXE SCOLAIRE")
            c.drawCentredString(149, 300, "IMMACULEE CONCEPTION")
            c.drawCentredString(149, 280, "DE LA CHARITE")
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(149, 260, "REÇU D'INSCRIPTION")

            c.setFont("Helvetica", 12)
            c.drawString(25, 240, f"Date : {date_inscription}")
            c.drawString(25, 220, f"Matricule : {matricule}")
            c.drawString(25, 200, f"Nom complet : {nom_complet}")
            c.drawString(25, 180, f"Classe : {classe}")
            c.drawString(25, 160, f"Responsable : {responsable}")
            c.drawString(25, 140, f"Téléphone : {telephone_responsable}")
            c.drawString(25, 120, f"Frais d'inscription : {frais_inscription} $")
            c.drawString(25, 100, f"Caissier(ère) : {caissier}")

            c.setFont("Helvetica-Oblique", 10)
            c.drawString(25, 70, "Merci pour votre confiance!")
            c.drawString(25, 50, "Veillez bien garder votre recu!")
            c.save()

            # 5. Redirection vers confirmation
            return render_template(
                'confirmation.html',
                nom_complet=nom_complet,
                matricule=matricule,
                classe=classe
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return "Une erreur est survenue lors de l'enregistrement."

    # Si GET
    return render_template('inscription.html')

#Route telechargemenr recu
@app.route('/telecharger_recu/<matricule>')
@login_required
def telecharger_recu_pdf(matricule):
    nom_fichier = f"recu_inscription_{matricule}.pdf"
    chemin_fichier = os.path.join(DOSSIER_RECUS, nom_fichier)

    if os.path.exists(chemin_fichier):
        return send_from_directory(DOSSIER_RECUS, nom_fichier)
    else:
        return f"Reçu introuvable pour le matricule {matricule}", 404

@app.route('/get_classes/<section>')
@login_required
def get_classes(section):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT classes.nom
        FROM classes
        JOIN sections ON classes.section_id = sections.id
        WHERE sections.nom = %s
    """, (section,))

    resultats = cursor.fetchall()
    conn.close()

    return jsonify([row[0] for row in resultats])

@app.route('/get_frais/<nom_classe>/<statut>')
@login_required
def get_frais(nom_classe, statut):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM classes WHERE nom = %s", (nom_classe,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'frais': 0})

        classe_id = result[0]

        cursor.execute("""
            SELECT montant FROM tarifs 
            WHERE classe_id = %s AND type = 'inscription' AND statut_eleve = %s
        """, (classe_id, statut.lower()))

        montant = cursor.fetchone()
        return jsonify({'frais': montant[0] if montant else 0})
    except mariadb.Error as e:
        print(f"Erreur MariaDB: {e}")
        return jsonify({'frais': 0})
    finally:
        if 'conn' in locals():
            conn.close()


@app.route('/liste', methods=['GET', 'POST'])
@login_required
def liste_eleves():
   
    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔹 Récupérer toutes les classes distinctes depuis la base de données
    cursor.execute("SELECT DISTINCT classe FROM eleves ORDER BY classe ASC")
    classes = [row[0] for row in cursor.fetchall()]

    # 🔹 Gérer les filtres
    classe = request.form.get('classe') if request.method == 'POST' else None
    recherche = request.form.get('recherche') if request.method == 'POST' else None

    if classe and recherche:
        cursor.execute("""
            SELECT * FROM eleves 
            WHERE classe = %s AND (nom LIKE %s OR postnom LIKE %s OR prenom LIKE %s)
        """, (classe, f'%{recherche}%', f'%{recherche}%', f'%{recherche}%'))
    elif classe:
        cursor.execute("SELECT * FROM eleves WHERE classe = %s", (classe,))
    elif recherche:
        cursor.execute("""
            SELECT * FROM eleves 
            WHERE nom LIKE %s OR postnom LIKE %s OR prenom LIKE %s
        """, (f'%{recherche}%', f'%{recherche}%', f'%{recherche}%'))
    else:
        cursor.execute("SELECT * FROM eleves")

    eleves = cursor.fetchall()
    conn.close()

    return render_template('liste.html', eleves=eleves, classe=classe or "", recherche=recherche or "", classes=classes)

@app.route('/telecharger_pdf/<classe>')
@login_required
def telecharger_pdf(classe):
    
    conn = get_db_connection()
    curseur = conn.cursor()
    curseur.execute("""
        SELECT matricule, nom, postnom, prenom, genre, classe, ecole_provenance, responsable, telephone_responsable, adresse 
        FROM eleves 
        WHERE classe = %s 
        ORDER BY nom ASC, postnom ASC, prenom ASC
    """, (classe,))

    eleves = curseur.fetchall()
    log_action("Telechargement liste enregistré", session['nom_utilisateur'])
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    def add_watermark(canvas, doc):
        #try:
            # Filigrane (au centre en arrière-plan)
            #watermark = ImageReader("static/l.jpg")
            #canvas.saveState()
            #canvas.translate(160, 370)
            #canvas.setFillAlpha(0.05)
            #canvas.drawImage(watermark, 0, 0, width=300, height=300, preserveAspectRatio=True, mask='auto')
            #canvas.restoreState()
        #except:
            #pass

        try:
            # Logo gauche
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 30, 740, width=60, height=60, mask='auto')

            # Logo droit
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg"))  # ton logo à droite
            canvas.drawImage(logo_droit, 500, 740, width=60, height=60, mask='auto')
        except Exception as e:
            print("Erreur lors de l'affichage des logos :", e)

    elements = []
    styles = getSampleStyleSheet()

    # 🔹 Logo et entête

    titre_ecole_style = ParagraphStyle(
        'TitreEcole',
        parent=styles['Title'],
        fontSize=20,  # 🔼 Taille du texte
        alignment=1,  # 1 = centré
        spaceAfter=40
    )
    elements.append(Paragraph(f"<b>COMPLEXE SCOLAIRE IMMACULEE CONCEPTION DE LA CHARITE</b>", titre_ecole_style))
    elements.append(Paragraph(f"📚 <b>Liste des élèves - Classe : {classe}</b>", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    # 🔹 Tableau
    data = [["Matricule", "Nom Complet", "Genre", "Classe", "Provenance", "Responsable", "Contact", "Adresse"]]
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]

    for e in eleves:
        nom_complet = f"{e[1]} {e[2]} {e[3]}"
        data.append([
            e[0],
            Paragraph(nom_complet, style_normal),
            e[4],
            Paragraph(e[5], style_normal),
            e[6] or "-",
            Paragraph(e[7], style_normal),
            e[8],
            Paragraph(e[9] or "-", style_normal)
    ])

    table = Table(data, colWidths=[65, 90, 50, 70, 60, 70, 70, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # 🔹 Pied de page
    date_gen = datetime.now().strftime("%d/%m/%Y à %Hh%M")
    elements.append(Paragraph(f"<i>Document généré le {date_gen}</i>", styles["Normal"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Signature du Directeur : ________", styles["Normal"]))

    doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)

    buffer.seek(0)
    return send_file(buffer, as_attachment=False, download_name=f"liste_{classe}.pdf", mimetype='application/pdf')

@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
def modifier_eleve(id):
    role = session.get('role_utilisateur', '')

    if role == 'lecture':
        flash("Vous n'avez pas les droits pour effectuer cette action.", "danger")
        return redirect(url_for('liste_eleves'))  # Ou vers une page où il peut juste consulter
    conn = get_db_connection()
    cursor = conn.cursor()
    # Récupérer l'élève
    cursor.execute("SELECT section FROM eleves WHERE id = %s", (id,))
    resultat = cursor.fetchone()

    if not resultat:
        flash("Élève introuvable", "danger")
        return redirect(url_for('liste_eleves'))

    section_eleve = resultat[0]
    role_utilisateur = session.get('role_utilisateur')

    # Vérification de la restriction
    if role_utilisateur != 'full' and role_utilisateur.lower() != section_eleve.lower():
        flash("Vous n'avez pas l'autorisation de modifier cet élève.", "danger")
        return redirect(url_for('liste_eleves'))
    if request.method == 'POST':
        nom = request.form['nom']
        postnom = request.form['postnom']
        prenom = request.form['prenom']
        genre = request.form['genre']
        section = request.form['section']
        classe = request.form['classe']
        annee_scolaire = request.form['annee_scolaire']
        lieu_naissance = request.form['lieu_naissance']
        date_naissance = request.form['date_naissance']
        ecole_provenance = request.form['ecole_provenance']
        classe_precedente = request.form['classe_precedente']
        #annee_precedente = request.form['annee_precedente']
        responsable = request.form['responsable']
        telephone_responsable = request.form['telephone_responsable']
        fonction_responsable = request.form['fonction_responsable']
        statut_eleve = request.form['statut_eleve']
        frais_inscription = request.form['frais_inscription']
        frais_bulletin = request.form['frais_bulletin']
        ram_papier = request.form['ram_papier']
        deux_savons = request.form['deux_savons']
        deux_ph = request.form['deux_ph']
        fournitures = request.form['fournitures']

        cursor.execute('''
            UPDATE eleves SET 
                nom = %s, postnom = %s, prenom = %s, genre = %s, section = %s, classe = %s, annee_scolaire = %s, 
                lieu_naissance = %s, date_naissance = %s, ecole_provenance = %s, classe_precedente = %s,
                responsable = %s, telephone_responsable = %s, fonction_responsable = %s, statut_eleve = %s, frais_inscription = %s, 
                frais_bulletin = %s, ram_papier = %s, deux_savons = %s, deux_ph = %s, fournitures = %s
            WHERE id = %s
        ''', (
            nom, postnom, prenom, genre, section, classe, annee_scolaire,
            lieu_naissance, date_naissance, ecole_provenance, classe_precedente,
            responsable, telephone_responsable, fonction_responsable, statut_eleve, frais_inscription,
            frais_bulletin, ram_papier, deux_savons, deux_ph, fournitures,
            id
        ))
        log_action("Modification eleve enregistré", session['nom_utilisateur'])
        conn.commit()
        conn.close()
        return redirect(url_for('liste_eleves'))

    # Pré-remplissage du formulaire
    cursor.execute("SELECT * FROM eleves WHERE id = %s", (id,))
    eleve = cursor.fetchone()
    conn.close()

    if eleve is None:
        return "Élève introuvable.", 404

    return render_template('modifier.html', eleve=eleve)

@app.route('/supprimer/<int:id>', methods=['GET'])
@login_required
def supprimer_eleve(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Récupération de la section de l'élève
    cursor.execute("SELECT section FROM eleves WHERE id = %s", (id,))
    result = cursor.fetchone()

    role_utilisateur = session.get('role_utilisateur', '').lower()

    if role_utilisateur != 'full':
        flash("Vous n'avez pas l'autorisation de supprimer cet élève.", "danger")
        return redirect(url_for('liste_eleves'))
    cursor.execute("DELETE FROM eleves WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    flash("Élève supprimé avec succès.", "success")
    log_action("Suppression eleve enregistré", session['nom_utilisateur'])
    return redirect(url_for('liste_eleves'))

@app.route("/gestion_minerval")
@login_required
def gestion_minerval():
    log_action("Acces gestion minerval enregistré", session['nom_utilisateur'])
    return render_template("gestion_minerval.html")


@app.route('/paiement', methods=['GET', 'POST'])
@login_required
def paiement():
    role = session.get('role_utilisateur', '')
    if role == 'lecture':
        return redirect(url_for('gestion_minerval'))
    
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Récupération données formulaire
            matricule = request.form['matricule']
            mois = request.form['mois']
            date_paiement = request.form['date_paiement']
            annee_scolaire = request.form['annee_scolaire']
            montant_paye = float(request.form['montant_paye'])
            mode_paiement = request.form.get('mode_paiement', 'Non spécifié')
            observation = request.form.get('observation', 'Aucun')
            mois_annee = ["Septembre", "Octobre", "Novembre", "Décembre",
                          "Janvier", "Février", "Mars", "Avril"]

            # Vérifier paiement mois précédent
            if mois in mois_annee:
                index_mois = mois_annee.index(mois)
                if index_mois > 0:
                    mois_precedent = mois_annee[index_mois - 1]
                    cursor.execute("""
                        SELECT SUM(montant_paye), MAX(montant_a_payer) 
                        FROM paiements 
                        WHERE matricule = %s AND mois = %s AND annee_scolaire = %s
                    """, (matricule, mois_precedent, annee_scolaire))
                    paiement_precedent = cursor.fetchone()
                    if (not paiement_precedent or paiement_precedent[0] is None or 
                        paiement_precedent[0] < paiement_precedent[1]):
                        flash(f"⛔ Paiement refusé : Le mois précédent ({mois_precedent}) n’a pas encore été réglé entièrement.", "danger")
                        return redirect(url_for('paiement'))

            # Infos élève
            cursor.execute("SELECT nom, postnom, prenom, genre, section, classe FROM eleves WHERE matricule = %s", (matricule,))
            eleve = cursor.fetchone()
            if not eleve:
                flash("Élève introuvable.", "danger")
                return redirect(url_for('paiement'))

            nom, postnom, prenom, genre, section, nom_classe = eleve
            nom_complet = f"{nom} {postnom} {prenom}"

            # Vérification autorisation
            role_utilisateur = session.get('role_utilisateur', '').lower()
            if role_utilisateur not in ['full', section.lower()]:
                flash(f"⚠️ Paiement refusé : votre profil n’a pas accès à la section « {section} ».", "danger")
                return redirect(url_for('paiement'))

            # Tarif minerval
            cursor.execute("SELECT id FROM classes WHERE nom = %s", (nom_classe,))
            classe_id_row = cursor.fetchone()
            if not classe_id_row:
                flash("Classe non reconnue dans le système.", "danger")
                return redirect(url_for('paiement'))
            classe_id = classe_id_row[0]

            cursor.execute("SELECT montant FROM tarifs WHERE classe_id = %s AND type = 'minerval'", (classe_id,))
            tarif_row = cursor.fetchone()
            if not tarif_row:
                flash("Aucun tarif enregistré pour cette classe.", "danger")
                return redirect(url_for('paiement'))

            montant_a_payer = float(tarif_row[0])
            montant_restant = montant_a_payer - montant_paye

            # Vérification doublon
            cursor.execute("""
                SELECT id FROM paiements 
                WHERE matricule = %s AND mois = %s AND annee_scolaire = %s
            """, (matricule, mois, annee_scolaire))
            paiement_existant = cursor.fetchone()
            if paiement_existant:
                flash(f"⚠️ Paiement déjà enregistré pour {mois} ({annee_scolaire}).", "warning")
                return redirect(url_for('paiement'))

            cursor.execute("""
                SELECT 1 FROM paiements
                WHERE matricule = %s AND mois = %s AND date_paiement = %s AND montant_paye = %s AND annee_scolaire = %s
            """, (matricule, mois, date_paiement, montant_paye, annee_scolaire))
            doublon = cursor.fetchone()
            if doublon:
                flash("Ce paiement semble déjà exister.", "warning")
                return redirect(url_for('paiement'))

            # Insertion paiement
            cursor.execute("""
                INSERT INTO paiements (
                    matricule, mois, annee_scolaire, montant_paye, montant_a_payer, montant_restant,
                    mode_paiement, date_paiement, observation
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                matricule, mois, annee_scolaire, montant_paye, montant_a_payer, montant_restant,
                mode_paiement, date_paiement, observation
            ))
            conn.commit()
            paiement_id = cursor.lastrowid

            # Téléphone responsable
            cursor.execute("SELECT telephone_responsable FROM eleves WHERE matricule = %s", (matricule,))
            resultat = cursor.fetchone()
            telephone_responsable = resultat[0] if resultat else None

            log_action("Paiement enregistré", session['nom_utilisateur'])

        except Exception as e:
            import traceback
            traceback.print_exc()
            flash("Erreur lors de l'enregistrement du paiement.", "danger")
            return redirect(url_for('paiement'))
        finally:
            if 'conn' in locals():
                conn.close()

        # Envoi SMS si numéro dispo
        if telephone_responsable:
            message = (f"C.S.Immaculée Conception de la Charité : Bonjour, nous confirmons le paiement de {montant_paye}$ "
                       f"du mois de {mois} pour l'élève {nom} {postnom} {prenom} ({matricule}). "
                       f"Le montant restant pour finaliser le paiement est de {montant_restant}$ Merci.")
            envoyer_sms(telephone_responsable, message)

        # Redirection confirmation
        return redirect(url_for('confirmation_paiement',
                                matricule=matricule,
                                nom_complet=nom_complet,
                                genre=genre,
                                mois=mois,
                                montant_paye=montant_paye,
                                montant_a_payer=montant_a_payer,
                                caissiere=observation,
                                paiement_id=paiement_id))
    else:
        # GET: afficher formulaire
        return render_template('paiement.html')

@app.route('/confirmation_paiement')
@login_required
def confirmation_paiement():
    # Ces données doivent être passées via redirect avec query string ou session selon ton choix
    matricule = request.args.get('matricule')
    nom_complet = request.args.get('nom_complet')
    genre = request.args.get('genre')
    mois = request.args.get('mois')
    montant_paye = float(request.args.get('montant_paye', 0))
    montant_a_payer = float(request.args.get('montant_a_payer', 0))
    caissiere = request.args.get('caissiere')
    paiement_id = request.args.get('paiement_id')  # utile pour téléchargement du reçu
    montant_restant = montant_a_payer - montant_paye

    return render_template('confirmation_paiement.html',
                           matricule=matricule,
                           nom_complet=nom_complet,
                           genre=genre,
                           mois=mois,
                           montant_paye=montant_paye,
                           montant_restant=montant_restant,
                           caissiere=caissiere,
                           paiement_id=paiement_id)

@app.route('/recu_paiement/<int:id>')
@login_required
def recu_paiement(id):
    role = session.get('role_utilisateur', '')

    if role == 'lecture':
        
        return redirect(url_for('gestion_minerval'))  # Ou vers une page où il peut juste consulter
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT p.*, e.nom, e.postnom, e.prenom, e.genre, e.classe 
            FROM paiements p
            JOIN eleves e ON p.matricule = e.matricule
            WHERE p.id = %s
        """, (id,))
        paiement = cursor.fetchone()
        conn.close()

        if not paiement:
            return "❌ Paiement introuvable", 404
        # ← Ici, tu ajoutes la sécurisation des montants
        montant_a_payer = float(paiement['montant_a_payer'] or 0)
        montant_paye = float(paiement['montant_paye'] or 0)
        montant_restant = montant_a_payer - montant_paye
        nom_complet = f"{paiement['nom']} {paiement['postnom']} {paiement['prenom']}"
        montant_restant = float(paiement['montant_a_payer']) - float(paiement['montant_paye'])
        
        filepath = os.path.join(DOSSIER_RECUS, "recu_paiement.pdf")
        if not os.path.exists(DOSSIER_RECUS):
            os.makedirs(DOSSIER_RECUS)

        # Supprime l'ancien PDF si besoin
        if os.path.exists(filepath):
            os.remove(filepath)

        c = canvas.Canvas(filepath, pagesize=A6)

        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droite = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche

                # Logos gauche et droite
            c.drawImage(logo_gauche, 15, 305, width=40, height=40, preserveAspectRatio=True, mask='auto')
            c.drawImage(logo_droite, 245, 305, width=40, height=40, preserveAspectRatio=True, mask='auto')
        except:
            pass
        # Filigrane
        #try:
                #logo = ImageReader("static/logo2.png")
                #c.saveState()
                #c.setFillAlpha(0.08)
                #c.drawImage(logo, 40, 100, width=240, height=240, preserveAspectRatio=True, mask='auto')
                #c.restoreState()
        #except:
                #pass

        # Texte
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(149, 320, "COMPLEXE SCOLAIRE")
        c.drawCentredString(149, 300, "IMMACULEE CONCEPTION")
        c.drawCentredString(149, 280, "DE LA CHARITE")
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(149, 260, "REÇU DE PAIEMENT")

        c.setFont("Helvetica", 12)
        c.drawString(25, 240, f"Date : {paiement['date_paiement']}")
        c.drawString(25, 220, f"Matricule : {paiement['matricule']}")
        c.drawString(25, 200, f"Nom complet : {nom_complet}")
        c.drawString(25, 180, f"Genre : {paiement['genre']}")
        c.drawString(25, 160, f"Classe : {paiement['classe']}")
        c.drawString(25, 140, f"Mois payé : {paiement['mois']}")
        c.drawString(25, 120, f"Montant payé : {float(paiement['montant_paye']):,.1f} $")
        c.drawString(25, 100, f"Montant restant : {montant_restant:,.1f} $")
        c.drawString(25, 80, f"Caissière : {paiement['observation']}")

        c.setFont("Helvetica-Oblique", 10)
        c.drawString(25, 50, "Merci pour votre confiance!")
        c.drawString(25, 40, "Veillez bien garder votre recu!")
        c.save()

        # ← Ici, ajoute la vérification
        if os.path.exists(filepath):
            return send_file(filepath)
        else:
            return "Le reçu n’a pas pu être généré.", 500

    except Exception as e:
        print("Erreur lors de la génération du reçu :", e)
        return "Une erreur s’est produite lors de la génération du reçu.", 500

@app.route('/infos_eleve/<matricule>')
@login_required
def infos_eleve(matricule):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Rechercher l'élève
    cursor.execute("SELECT nom, postnom, prenom, genre, section, classe, annee_scolaire FROM eleves WHERE matricule = %s", (matricule,))
    eleve = cursor.fetchone()

    if not eleve:
        conn.close()
        return jsonify({'error': 'Élève introuvable'}), 404

    nom = eleve['nom']
    postnom = eleve['postnom']
    prenom = eleve['prenom']
    genre = eleve['genre']
    section = eleve['section']
    nom_classe = eleve['classe']
    annee_scolaire = eleve['annee_scolaire']


    # Trouver l'ID de la classe
    cursor.execute("SELECT id FROM classes WHERE nom = %s", (nom_classe,))
    classe_row = cursor.fetchone()
    if not classe_row:
        conn.close()
        return jsonify({'error': 'Classe introuvable'}), 404

    classe_id = classe_row['id']

    # Trouver le montant du minerval
    cursor.execute("SELECT montant FROM tarifs WHERE classe_id = %s AND type = 'minerval'", (classe_id,))
    tarif_row = cursor.fetchone()
    if not tarif_row:
        conn.close()
        return jsonify({'error': 'Tarif introuvable'}), 404

    montant = float(tarif_row['montant'])
    conn.close()

    # Retourner les données au frontend
    return jsonify({
        'nom': nom,
        'postnom': postnom,
        'prenom': prenom,
        'genre': genre,
        'section': section,
        'classe': nom_classe,
        'montant': montant,
        'annee_scolaire' : annee_scolaire
    })

@app.route('/historique_paiements', methods=['GET', 'POST'])
@login_required
def historique_paiements():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 🔍 Récupération des valeurs uniques pour les listes déroulantes
    cursor.execute("SELECT DISTINCT classe FROM eleves")
    classes = [row['classe'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT section FROM eleves")
    sections = [row['section'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT mois FROM paiements")
    mois_disponibles = [row['mois'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT observation FROM paiements WHERE observation IS NOT NULL")
    caissiers = [row['observation'] for row in cursor.fetchall()]

    # Récupération des filtres envoyés via formulaire
    # Fonction utilitaire pour récupérer depuis POST ou GET
    def get_filter_value(key):
        return (request.form.get(key) or request.args.get(key) or '').strip()

    # Récupération des filtres
    filtre_matricule = get_filter_value('filtre_matricule')
    filtre_classe = get_filter_value('filtre_classe')
    filtre_ordre = get_filter_value('filtre_ordre')
    filtre_mois = get_filter_value('filtre_mois')
    filtre_jour = get_filter_value('filtre_jour')
    filtre_caissier = get_filter_value('filtre_caissier')
    # Construction dynamique de la requête SQL avec filtres
    requete = """
        SELECT p.*, e.nom, e.postnom, e.prenom, e.classe, e.section
        FROM paiements p
        JOIN eleves e ON p.matricule = e.matricule
        WHERE 1=1
    """
    params = []

    if filtre_matricule:
        requete += " AND p.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")

    if filtre_classe:
        requete += " AND e.classe = %s"
        params.append(filtre_classe)

    if filtre_ordre == "Oui":
        requete += " AND CAST(p.montant_paye AS FLOAT) >= CAST(p.montant_a_payer AS FLOAT)"
    elif filtre_ordre == "Non":
        requete += " AND CAST(p.montant_paye AS FLOAT) < CAST(p.montant_a_payer AS FLOAT)"

    if filtre_mois:
        requete += " AND p.mois = %s"
        params.append(filtre_mois)

    if filtre_jour:
        requete += " AND p.date_paiement = %s"
        params.append(filtre_jour)

    if filtre_caissier:
        requete += " AND p.observation = %s"
        params.append(filtre_caissier)

    requete += " ORDER BY p.date_paiement DESC"

    cursor.execute(requete, params)
    paiements = cursor.fetchall()

    # Formatage des données
    paiements_formates = []
    for paiement in paiements:
        try:
            montant_paye = float(paiement['montant_paye'] or 0)
        except:
            montant_paye = 0.0

        try:
            montant_a_payer = float(paiement['montant_a_payer'] or 0)
        except:
            montant_a_payer = 0.0

        ordre = "Oui" if montant_paye >= montant_a_payer else "Non"

        paiements_formates.append({
            'id': paiement['id'],
            'matricule': paiement['matricule'],
            'nom_complet': f"{paiement['nom']} {paiement['postnom']} {paiement['prenom']}",
            'classe': paiement['classe'],
            'section': paiement['section'],
            'mois': paiement['mois'],
            'date': paiement['date_paiement'],
            'montant_a_payer': montant_a_payer,
            'montant_paye': montant_paye,
            'mode_paiement': paiement['mode_paiement'],
            'caissiere': paiement['observation'],
            'ordre': ordre
        })

    conn.close()

    return render_template(
        "historique_paiements.html",
        paiements=paiements_formates,
        classes=classes,
        sections=sections,
        mois_disponibles=mois_disponibles,
        filtre_matricule=filtre_matricule,
        filtre_classe=filtre_classe,
        filtre_ordre=filtre_ordre,
        filtre_mois=filtre_mois,
        filtre_jour=filtre_jour,
        filtre_caissier=filtre_caissier,
        caissiers=caissiers
    )


@app.route('/telecharger_historique_paiement')
@login_required
def telecharger_historique_paiement():
    # Récupération des filtres
    filtre_matricule = request.values.get('filtre_matricule', '').strip()
    filtre_classe    = request.values.get('filtre_classe', '')
    filtre_mois      = request.values.get('filtre_mois', '')
    filtre_jour      = request.values.get('filtre_jour', '')
    filtre_caissier  = request.values.get('filtre_caissier', '')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
   
    # Requête SQL dynamique avec filtres
    query = """
        SELECT p.*, e.nom, e.postnom, e.prenom, e.classe, e.section
        FROM paiements p
        JOIN eleves e ON p.matricule = e.matricule
        WHERE 1=1
    """
    params = []

    if filtre_matricule:
        query += " AND p.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")

    if filtre_classe:
        query += " AND e.classe = %s"
        params.append(filtre_classe)

    if filtre_mois:
        query += " AND p.mois = %s"
        params.append(filtre_mois)

    if filtre_jour:
        query += " AND p.date_paiement = %s"
        params.append(filtre_jour)

    if filtre_caissier:
        query += " AND p.observation = %s"
        params.append(filtre_caissier)

    query += " ORDER BY p.date_paiement DESC"
    cursor.execute(query, params)
    paiements = cursor.fetchall()  # car fetchall() sans argument
    cursor.close()
    conn.close()

    # 🔽 Création du fichier PDF
    filepath = os.path.join(DOSSIER_RECUS, "historique_paiements.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)


    largeur, hauteur = landscape(A4)
    styles = getSampleStyleSheet()

    data = [
        ["N°", "Matricule", "Nom complet", "Classe", "Section", "Mois", "Date", "Payé", "À payer", "Ordre", "Caissier(ère)"]
    ]

    total_recu = 0  # 👉 Initialiser le total payé filtré

    for i, p in enumerate(paiements, start=1):
        nom_complet = f"{p['nom']} {p['postnom']} {p['prenom']}"
        montant_paye = float(p['montant_paye'] or 0)
        montant_a_payer = float(p['montant_a_payer'] or 0)
        ordre = "Oui" if montant_paye >= montant_a_payer else "Non"

        total_recu += montant_paye  # 👉 Ajouter au total filtré

        data.append([
            str(i),
            Paragraph(p['matricule'], styles["Normal"]),
            Paragraph(nom_complet, styles["Normal"]),
            Paragraph(p['classe'], styles["Normal"]),
            p['section'],
            p['mois'],
            p['date_paiement'],
            f"{montant_paye:,.1f} $",
            f"{montant_a_payer:,.1f} $",
            ordre,
            Paragraph(p['observation'] or "", styles["Normal"])
        ])

    table = Table(data, colWidths=[30, 70, 140, 80, 50, 50, 65, 70, 70, 40, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    # ➕ Ajouter une ligne de résumé du total reçu
    total_data = [["", "", "", "", "", "", "Total reçu :", f"{total_recu:,.1f} $", "", "", ""]]
    total_table = Table(total_data, colWidths=[30, 70, 140, 80, 50, 50, 65, 70, 70, 40, 70])
    total_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (6, 0)),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (6, 0), (7, 0), colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (6, 0), (7, 0), 'RIGHT'),
    ]))

    def entete(canvas, doc):
        canvas.saveState()

        # 🔹 Images gauche et droite
        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 60, hauteur - 80, width=60, height=60, mask='auto')
            canvas.drawImage(logo_droit, largeur - 120, hauteur - 80, width=60, height=60, mask='auto')
        except:
            pass
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(largeur / 2, hauteur - 40, "COMPLEXE SCOLAIRE IMMACULÉE CONCEPTION DE LA CHARITÉ")
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(largeur / 2, hauteur - 60, "HISTORIQUE DES PAIEMENTS")

        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(largeur - 60, hauteur - 15, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        canvas.setFont("Helvetica", 12)
        y = hauteur - 110
        canvas.drawString(60, y, f"Classe : {filtre_classe or '---'}")
        canvas.drawString(250, y, f"Mois : {filtre_mois or '---'}")
        canvas.drawString(410, y, f"Jour : {filtre_jour or '---'}")
        canvas.drawString(580, y, f"Caissier : {filtre_caissier or '---'}")
        canvas.restoreState()

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), topMargin=130, leftMargin=25, rightMargin=25, bottomMargin=40)
    elements = [table, Spacer(1, 12), total_table]

    doc.build(elements, onFirstPage=entete, onLaterPages=entete)

    return send_file(filepath, as_attachment=False)

##---------------------------------------------------------------
@app.route('/eleves_non_en_ordre', methods=['GET', 'POST'])
@login_required
def eleves_non_en_ordre():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Récupération des valeurs uniques pour les filtres
    cursor.execute("SELECT DISTINCT classe FROM eleves")
    classes = [row['classe'] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT mois FROM paiements")
    mois_disponibles = [row['mois'] for row in cursor.fetchall()]

    filtre_matricule = request.form.get('filtre_matricule', '').strip()
    filtre_classe = request.form.get('filtre_classe', '')
    filtre_mois = request.form.get('filtre_mois', '')

    # Requête SQL pour récupérer les élèves avec paiements partiels
    query = """
        SELECT 
            e.nom, e.postnom, e.prenom, e.matricule, e.classe, e.section,
            p.mois,
            SUM(p.montant_paye) AS total_montant_paye,
            p.montant_a_payer,
            MAX(p.date_paiement) AS date_paiement
        FROM paiements p
        JOIN eleves e ON e.matricule = p.matricule
        WHERE 1=1
    """
    params = []

    # Filtres
    if filtre_matricule:
        query += " AND p.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")
    if filtre_classe:
        query += " AND e.classe = %s"
        params.append(filtre_classe)
    if filtre_mois:
        query += " AND p.mois = %s"
        params.append(filtre_mois)

    query += """
        GROUP BY p.matricule, p.mois
        HAVING total_montant_paye < montant_a_payer
        ORDER BY date_paiement DESC
    """
    cursor.execute(query, params)
    resultats = cursor.fetchall()
    conn.close()

    # Renommer les champs pour correspondre à ceux utilisés dans le template HTML
    resultats_formates = []
    for row in resultats:
        resultats_formates.append({
            'nom': row['nom'],
            'postnom': row['postnom'],
            'prenom': row['prenom'],
            'matricule': row['matricule'],
            'classe': row['classe'],
            'section': row['section'],
            'mois': row['mois'],
            'montant_paye': row['total_montant_paye'],
            'montant_a_payer': row['montant_a_payer'],
            'date_paiement': row['date_paiement']
        })

    return render_template(
        'eleves_non_en_ordre.html',
        resultats=resultats_formates,
        classes=classes,
        mois_disponibles=mois_disponibles,
        filtre_matricule=filtre_matricule,
        filtre_classe=filtre_classe,
        filtre_mois=filtre_mois
    )


@app.route('/telecharger_non_en_ordre')
@login_required
def telecharger_non_en_ordre():
    filtre_matricule = request.args.get('filtre_matricule', '').strip()
    filtre_classe = request.args.get('filtre_classe', '')
    filtre_mois = request.args.get('filtre_mois', '')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = """
        SELECT e.nom, e.postnom, e.prenom, e.matricule, e.classe, e.section,
               p.mois,
               MAX(CAST(p.montant_a_payer AS FLOAT)) AS total_a_payer,
               SUM(CAST(p.montant_paye AS FLOAT)) AS total_paye,
               MAX(p.date_paiement) AS derniere_date
        FROM paiements p
        JOIN eleves e ON e.matricule = p.matricule
        WHERE 1=1
    """
    params = []

    if filtre_matricule:
        query += " AND p.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")
    if filtre_classe:
        query += " AND e.classe = %s"
        params.append(filtre_classe)
    if filtre_mois:
        query += " AND p.mois = %s"
        params.append(filtre_mois)

    query += """
        GROUP BY e.nom, e.postnom, e.prenom, e.matricule, e.classe, e.section, p.mois
        HAVING total_paye + 0.01 < total_a_payer

    """


    cursor.execute(query, params)
    resultats = cursor.fetchall()
    conn.close()

    # Création du PDF
    filepath = os.path.join(DOSSIER_RECUS, "eleves_partiellement_en_ordre.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)

    largeur, hauteur = landscape(A4)
    styles = getSampleStyleSheet()

    data = [
        ["N°", "Matricule", "Nom complet", "Classe", "Section", "Mois", "Montant payé", "À payer", "Date"]
    ]

    for i, r in enumerate(resultats, start=1):
        nom_complet = f"{r['nom']} {r['postnom']} {r['prenom']}"
        data.append([
            str(i),
            Paragraph(r['matricule'], styles["Normal"]),
            Paragraph(nom_complet, styles["Normal"]),
            Paragraph(r['classe'], styles["Normal"]),
            r['section'],
            r['mois'],
            f"{r['total_paye']:,.1f} $",
            f"{r['total_a_payer']:,.1f} $",
            r['derniere_date']
        ])

    table = Table(data, colWidths=[30, 90, 170, 110, 70, 70, 80, 60, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    def entete(canvas, doc):
        canvas.saveState()
        
        # 🔹 Images gauche et droite
        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 60, hauteur - 80, width=60, height=60, mask='auto')


            canvas.drawImage(logo_droit, largeur - 120, hauteur - 80, width=60, height=60, mask='auto')
        except:
            pass
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(largeur / 2, hauteur - 40, "COMPLEXE SCOLAIRE IMMACULEE CONCEPTION DE LA CHARITE")
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(largeur / 2, hauteur - 60, "ELEVES PARTIELLEMENT EN ORDRE")

        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(largeur - 60, hauteur - 15, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        canvas.setFont("Helvetica", 12)
        y = hauteur - 110
        canvas.drawString(60, y, f"Classe : {filtre_classe or '---'}")
        canvas.drawString(370, y, f"Mois : {filtre_mois or '---'}")
        canvas.drawString(570, y, f"Matricule : {filtre_matricule or '---'}")
        canvas.restoreState()

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), topMargin=130, leftMargin=25, rightMargin=25, bottomMargin=40)
    doc.build([table], onFirstPage=entete, onLaterPages=entete)

    return send_file(filepath, as_attachment=False)

@app.route('/recu_finalisation/<matricule>/<mois>')
@login_required
def recu_finalisation(matricule, mois):
    filepath = os.path.join(DOSSIER_RECUS, "recu_finalisation.pdf")

    if not os.path.exists(filepath):
        return "Reçu introuvable", 404

    return send_file(filepath, mimetype='application/pdf')

@app.route('/finaliser_paiement/<matricule>/<mois>', methods=['GET', 'POST'])
@login_required
def finaliser_paiement(matricule, mois):

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 🔍 Récupérer le paiement partiel existant
    cursor.execute("""
        SELECT p.*, e.nom, e.postnom, e.prenom, e.classe, e.section, e.genre
        FROM paiements p
        JOIN eleves e ON p.matricule = e.matricule
        WHERE p.matricule = %s AND p.mois = %s
    """, (matricule, mois))
    paiement = cursor.fetchone()

    if not paiement:
        conn.close()
        return "Paiement introuvable", 404
    nom_complet = f"{paiement['nom']} {paiement['postnom']} {paiement['prenom']}"
    cursor.execute("""
        SELECT SUM(montant_paye) as total
        FROM paiements
        WHERE matricule = %s AND mois = %s AND annee_scolaire = %s
    """, (matricule, mois, paiement['annee_scolaire']))
    somme_paye = cursor.fetchone()

    montant_paye_total = float(somme_paye['total'] or 0)
    montant_a_payer = float(paiement['montant_a_payer'] or 0)
    montant_restant = montant_a_payer - montant_paye_total

    cursor.execute("SELECT section FROM eleves WHERE matricule = %s", (matricule,))
    section_row = cursor.fetchone()
    if section_row:
        section = section_row['section']

        role_utilisateur = session.get('role_utilisateur', '').lower()
        if role_utilisateur not in ['full', section.lower()]:
            return redirect(url_for('eleves_non_en_ordre'))

    nom_caissier = session.get('nom_utilisateur', 'inconnu')

    if request.method == 'POST':
        try:
            montant_complement = float(request.form['montant_complement'])
        except:
            montant_complement = 0.0

        date_paiement = request.form['date_paiement']
        mode_paiement = request.form['mode_paiement']
        observation = nom_caissier
        nouveau_montant = montant_paye_total + montant_complement
        annee_scolaire = paiement['annee_scolaire']

        cursor.execute("""
            SELECT 1 FROM paiements
            WHERE matricule = %s AND mois = %s AND date_paiement = %s AND montant_paye = %s AND annee_scolaire = %s
        """, (matricule, mois, date_paiement, montant_complement, annee_scolaire))
        doublon = cursor.fetchone()

        if doublon:
            conn.close()
            flash("Ce paiement a déjà été enregistré.", "warning")
            return redirect(url_for('finaliser_paiement', matricule=matricule, mois=mois))

        cursor.execute("""
            INSERT INTO paiements (
                matricule, mois, montant_a_payer, montant_paye,
                mode_paiement, date_paiement, observation, annee_scolaire
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            paiement['matricule'],
            paiement['mois'],
            paiement['montant_a_payer'],
            montant_complement,
            mode_paiement,
            date_paiement,
            observation,
            paiement['annee_scolaire']
        ))
        log_action("Finalisation Paiement enregistré", session['nom_utilisateur'])
        conn.commit()

        montant_restant = montant_a_payer - (montant_paye_total + montant_complement)
        message = f"C.S.Immaculée Conception de la Charité : Bonjour, nous confirmons la finalisation du paiement de {montant_complement}$ pour le mois de {mois} concernant l'élève {paiement['nom']} {paiement['postnom']} {paiement['prenom']} ({matricule}). Le montant restant pour finaliser le paiement est de {montant_restant}$ Merci."

        cursor.execute("SELECT telephone_responsable FROM eleves WHERE matricule = %s", (matricule,))
        tel_row = cursor.fetchone()
        if tel_row:
            telephone_responsable = tel_row['telephone_responsable']
            envoyer_sms(telephone_responsable, message)

        conn.close()

        # ✅ Génération automatique du reçu
        filepath = os.path.join(DOSSIER_RECUS, "recu_finalisation.pdf")
        if not os.path.exists(DOSSIER_RECUS):
            os.makedirs(DOSSIER_RECUS)

        # Supprime l'ancien PDF si besoin
        if os.path.exists(filepath):
            os.remove(filepath)

        c = canvas.Canvas(filepath, pagesize=A6)

        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droite = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            c.drawImage(logo_gauche, 15, 305, width=40, height=40, preserveAspectRatio=True, mask='auto')
            c.drawImage(logo_droite, 245, 305, width=40, height=40, preserveAspectRatio=True, mask='auto')
        except:
            pass

        #try:
            #logo = ImageReader("static/logo2.png")
            #c.saveState()
            #c.setFillAlpha(0.08)
            #c.drawImage(logo, 40, 100, width=240, height=240, preserveAspectRatio=True, mask='auto')
            #c.restoreState()
        #except:
            #pass

        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(149, 320, "COMPLEXE SCOLAIRE")
        c.drawCentredString(149, 300, "IMMACULEE CONCEPTION")
        c.drawCentredString(149, 280, "DE LA CHARITE")
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(149, 260, "REÇU DE PAIEMENT(FINALISATION)")
        c.setFont("Helvetica", 12)
        c.drawString(25, 240, f"Date : {date_paiement}")
        c.drawString(25, 220, f"Matricule : {paiement['matricule']}")
        c.drawString(25, 200, f"Nom complet : {nom_complet}")
        c.drawString(25, 180, f"Genre : {paiement['genre']}")
        c.drawString(25, 160, f"Classe : {paiement['classe']}")
        c.drawString(25, 140, f"Mois payé : {mois}")
        c.drawString(25, 120, f"Montant payé : {montant_complement:,.1f} $")
        c.drawString(25, 100, f"Montant restant : {montant_restant:,.1f} $")
        c.drawString(25, 80, f"Caissier(ère) : {observation}")
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(25, 50, "Merci pour votre confiance!")
        c.drawString(25, 40, "Veillez bien garder votre reçu!")
        c.save()

        return redirect(url_for('imprimer_pdf') + '?url=' + url_for('recu_finalisation', matricule=matricule, mois=mois))

    conn.close()
    return render_template("finaliser_paiement.html",
                           paiement=paiement,
                           montant_restant=montant_restant,
                           montant_paye_total=montant_paye_total,
                           nom_caissier=nom_caissier,
                           current_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/eleves_en_ordre', methods=['GET', 'POST'])
@login_required
def eleves_en_ordre():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    filtre_matricule = ''
    filtre_classe = ''
    filtre_mois = ''

    # Pour les filtres
    cursor.execute("SELECT DISTINCT classe FROM eleves")
    classes = [row['classe'] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT mois FROM paiements")
    mois = [row['mois'] for row in cursor.fetchall()]
    # Requête de base
    query = """
        SELECT e.matricule, e.nom, e.postnom, e.prenom, e.classe, e.section,
               p.mois, SUM(p.montant_paye) AS montant_paye,
               p.montant_a_payer, MAX(p.date_paiement) as date_paiement
        FROM paiements p
        JOIN eleves e ON p.matricule = e.matricule
        WHERE 1=1
    """
    params = []

    # 🔍 Filtres dynamiques
    if request.method == 'POST':
        filtre_matricule = request.form.get('filtre_matricule', '').strip()
        filtre_classe = request.form.get('filtre_classe', '')
        filtre_mois = request.form.get('filtre_mois', '')

    if filtre_matricule:
        query += " AND e.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")

    if filtre_classe:
        query += " AND e.classe = %s"
        params.append(filtre_classe)

    if filtre_mois:
        query += " AND p.mois = %s"
        params.append(filtre_mois)

    # 🔄 Groupement
    query += " GROUP BY e.matricule, p.mois"

    # ✅ Filtrer ceux qui ont payé en totalité
    query = f"""
        SELECT * FROM (
            {query}
        ) AS sous_requete
        WHERE montant_paye >= montant_a_payer
    """


    cursor.execute(query, params)
    resultats = cursor.fetchall()
    conn.close()

    return render_template('eleves_en_ordre.html',
                           resultats=resultats,
                           filtre_matricule=filtre_matricule,
                           filtre_classe=filtre_classe,
                           filtre_mois=filtre_mois,
                           classes=classes,
                           mois_disponibles=mois)

@app.route('/telecharger_eleves_en_ordre')
@login_required
def telecharger_eleves_en_ordre():
    # Récupération des filtres
    filtre_matricule = request.args.get('filtre_matricule', '').strip()
    filtre_classe = request.args.get('filtre_classe', '')
    filtre_mois = request.args.get('filtre_mois', '')
    filtre_jour = request.args.get('filtre_jour', '')
    filtre_caissier = request.args.get('filtre_caissier', '')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Requête SQL dynamique avec filtres
    query = """
        SELECT 
            p.matricule,
            e.nom, e.postnom, e.prenom, e.classe, e.section,
            p.mois, 
            MAX(p.date_paiement) AS date_paiement,
            SUM(p.montant_paye) AS montant_paye,
            MAX(p.montant_a_payer) AS montant_a_payer,
            p.observation
        FROM paiements p
        JOIN eleves e ON p.matricule = e.matricule
        WHERE 1=1

    """
    params = []

    if filtre_matricule:
        query += " AND p.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")

    if filtre_classe:
        query += " AND e.classe = %s"
        params.append(filtre_classe)

    if filtre_mois:
        query += " AND p.mois = %s"
        params.append(filtre_mois)

    if filtre_jour:
        query += " AND p.date_paiement = %s"
        params.append(filtre_jour)

    if filtre_caissier:
        query += " AND p.observation = %s"
        params.append(filtre_caissier)

    query += " GROUP BY p.matricule, p.mois HAVING SUM(p.montant_paye) >= MAX(p.montant_a_payer) ORDER BY p.date_paiement DESC"
    
    cursor.execute(query, params)
    paiements = cursor.fetchall()
    conn.close()

    # Création du fichier PDF
    filepath = os.path.join(DOSSIER_RECUS, "eleves_en_ordre.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)

    largeur, hauteur = landscape(A4)
    styles = getSampleStyleSheet()

    data = [
        ["N°", "Matricule", "Nom complet", "Classe", "Section", "Mois", "Ordre", "Caissière"]
    ]

    for i, p in enumerate(paiements, start=1):
        nom_complet = f"{p['nom']} {p['postnom']} {p['prenom']}"
        montant_paye = float(p['montant_paye'] or 0)
        montant_a_payer = float(p['montant_a_payer'] or 0)
        ordre = "Oui" if montant_paye >= montant_a_payer else "Non"

        # 📌 Saut de ligne : on utilise Paragraph
        data.append([
            str(i),
            Paragraph(p['matricule'], styles["Normal"]),
            Paragraph(nom_complet, styles["Normal"]),
            Paragraph(p['classe'], styles["Normal"]),
            p['section'],
            p['mois'],
            ordre,
            Paragraph(p['observation'] or "", styles["Normal"])
        ])

    table = Table(data, colWidths=[30, 90, 180, 150, 60, 65, 50, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    def entete(canvas, doc):
        canvas.saveState()
        
        # 🔹 Images gauche et droite
        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 60, hauteur - 80, width=60, height=60, mask='auto')

            canvas.drawImage(logo_droit, largeur - 120, hauteur - 80, width=60, height=60, mask='auto')
        except:
            pass
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(largeur / 2, hauteur - 40, "COMPLEXE SCOLAIRE IMMACULEE CONCEPTION DE LA CHARITE")
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(largeur / 2, hauteur - 60, "ELEVES EN ORDRE")

        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(largeur - 60, hauteur - 15, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        canvas.setFont("Helvetica", 12)
        y = hauteur - 110
        canvas.drawString(60, y, f"Classe : {filtre_classe or '---'}")
        canvas.drawString(260, y, f"Mois : {filtre_mois or '---'}")
        canvas.drawString(450, y, f"Jour : {filtre_jour or '---'}")
        canvas.drawString(600, y, f"Caissier : {filtre_caissier or '---'}")
        canvas.restoreState()

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), topMargin=130, leftMargin=25, rightMargin=25, bottomMargin=40)
    elements = [table]

    doc.build(elements, onFirstPage=entete, onLaterPages=entete)

    return send_file(filepath, as_attachment=False)

@app.route('/eleves_sans_paiement', methods=['GET', 'POST'])
@login_required
def eleves_sans_paiement():
    filtre_matricule = ''
    filtre_classe = ''
    filtre_mois = ''
    mois_disponibles = [ "Septembre", "Octobre", "Novembre", "Décembre","Janvier", "Février", "Mars", "Avril"]

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 📌 Récupérer toutes les classes pour la sélection
    cursor.execute("SELECT DISTINCT classe FROM eleves")
    classes = [row['classe'] for row in cursor.fetchall()]

    if request.method == 'POST':
        filtre_matricule = request.form.get('filtre_matricule', '').strip()
        filtre_classe = request.form.get('filtre_classe', '')
        filtre_mois = request.form.get('filtre_mois', '')

    # 🧠 Requête : ÉLÈVES QUI N'ONT PAS DE PAIEMENT POUR LE MOIS CHOISI
    query = """
        SELECT e.*
        FROM eleves e
        WHERE NOT EXISTS (
            SELECT 1 FROM paiements p
            WHERE p.matricule = e.matricule AND p.mois = %s
        )
    """
    params = [filtre_mois or ""]

    if filtre_matricule:
        query += " AND e.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")

    if filtre_classe:
        query += " AND e.classe = %s"
        params.append(filtre_classe)

    cursor.execute(query, params)
    resultats = cursor.fetchall()
    conn.close()

    return render_template("eleves_sans_paiement.html",
                           resultats=resultats,
                           filtre_matricule=filtre_matricule,
                           filtre_classe=filtre_classe,
                           filtre_mois=filtre_mois,
                           classes=classes,
                           mois_disponibles=mois_disponibles)

@app.route('/telecharger_sans_paiement')
@login_required
def telecharger_sans_paiement():
    filtre_matricule = request.args.get('filtre_matricule', '').strip()
    filtre_classe = request.args.get('filtre_classe', '')
    filtre_mois = request.args.get('filtre_mois', '')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Tous les élèves
    cursor.execute("SELECT * FROM eleves")
    tous_les_eleves = cursor.fetchall()


    # Tous les paiements selon les filtres
    query_paiement = """
        SELECT DISTINCT matricule FROM paiements WHERE 1=1
    """
    params = []

    if filtre_mois:
        query_paiement += " AND mois = %s"
        params.append(filtre_mois)

    if filtre_classe:
        query_paiement += " AND matricule IN (SELECT matricule FROM eleves WHERE classe = %s)"
        params.append(filtre_classe)

    if filtre_matricule:
        query_paiement += " AND matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")

    cursor.execute(query_paiement, params)
    paiements = cursor.fetchall()
    matricules_payes = set([p['matricule'] for p in paiements])

    # Filtrer les élèves sans paiement
    eleves_sans_paiement = []
    for e in tous_les_eleves:
        if e['matricule'] not in matricules_payes:
            if (not filtre_classe or e['classe'] == filtre_classe) and \
               (not filtre_matricule or filtre_matricule.lower() in e['matricule'].lower()):
                eleves_sans_paiement.append(e)

    conn.close()

    # Création du fichier PDF

    filepath = os.path.join(DOSSIER_RECUS, "eleves_sans_paiement.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)

    largeur, hauteur = landscape(A4)
    styles = getSampleStyleSheet()

    data = [["N°", "Matricule", "Nom complet", "Genre", "Classe", "Section"]]
    for i, e in enumerate(eleves_sans_paiement, start=1):
        nom_complet = f"{e['nom']} {e['postnom']} {e['prenom']}"
        data.append([
            str(i),
            e['matricule'],
            Paragraph(nom_complet, styles["Normal"]),
            e['genre'],
            Paragraph(e['classe'], styles["Normal"]),
            e['section']
        ])

    table = Table(data, colWidths=[50, 120, 200, 80, 170, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    def entete(canvas, doc):
        canvas.saveState()
        # 🔹 Images gauche et droite
        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 60, hauteur - 80, width=60, height=60, mask='auto')

            canvas.drawImage(logo_droit, largeur - 120, hauteur - 80, width=60, height=60, mask='auto')
        except:
            pass

        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(largeur / 2, hauteur - 40, "COMPLEXE SCOLAIRE IMMACULEE CONCEPTION DE LA CHARITE")
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(largeur / 2, hauteur - 60, "ÉLÈVES SANS PAIEMENT")

        canvas.setFont("Helvetica", 12)
        canvas.drawRightString(largeur - 60, hauteur - 15, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.drawString(60, hauteur - 100, f"Classe : {filtre_classe or '---'}")
        canvas.drawString(300, hauteur - 100, f"Mois : {filtre_mois or '---'}")
        canvas.drawString(500, hauteur - 100, f"Matricule : {filtre_matricule or '---'}")
        canvas.restoreState()

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), topMargin=130, leftMargin=25, rightMargin=25, bottomMargin=40)
    elements = [table]
    doc.build(elements, onFirstPage=entete, onLaterPages=entete)

    return send_file(filepath, as_attachment=False)

@app.route('/statistiques_paiements', methods=['GET'])
@login_required
def statistiques_paiements():
    mois = request.args.get('mois', '')
    classe = request.args.get('classe', '')
    section = request.args.get('section', '')
    annee_scolaire = request.args.get('annee_scolaire', '')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Requête principale avec ajout de nb_ayant_paye
    query = """
        SELECT 
            e.classe,
            s.nom AS section,
            %s AS mois,
            COUNT(DISTINCT e.matricule) AS nb_eleves,
            COUNT(DISTINCT p.matricule) AS nb_ayant_paye,
            COALESCE(SUM(p.montant_paye), 0) AS total_paye,
            t.montant AS tarif_minerval,
            COALESCE(t.montant * COUNT(DISTINCT e.matricule), 0) AS total_attendu
        FROM eleves e
        JOIN classes c ON e.classe = c.nom
        JOIN sections s ON c.section_id = s.id
        LEFT JOIN paiements p ON e.matricule = p.matricule
            AND (%s = '' OR p.mois = %s)
            AND (%s = '' OR p.annee_scolaire = %s)
        LEFT JOIN tarifs t ON t.classe_id = c.id AND t.type = 'minerval'
        WHERE (%s = '' OR e.classe = %s)
        AND (%s = '' OR s.nom = %s)
        GROUP BY e.classe, s.nom, t.montant
        ORDER BY e.classe
    """

    params = [
        mois,
        mois, mois,
        annee_scolaire, annee_scolaire,
        classe, classe,
        section, section
    ]

    cursor.execute(query, params)
    statistiques=cursor.fetchall()

    nb_mois_par_annee = 8  # nombre de mois de Septembre à Avril
    total_attendu_global = 0

    for stat in statistiques:
        montant_tarif = stat["tarif_minerval"] or 0
        nb_eleves = stat["nb_eleves"] or 0

        if mois == '' and annee_scolaire != '':
            # Si on filtre par année scolaire (sans mois), on multiplie par le nombre de mois
            total_attendu_global += montant_tarif * nb_eleves * nb_mois_par_annee
        else:
            # Sinon montant attendu simple (par mois)
            total_attendu_global += montant_tarif * nb_eleves


    # Total global
    total_paye_global = sum(float(r["total_paye"]) for r in statistiques)
    #total_attendu_global = sum(float(r["total_attendu"]) for r in statistiques)
    ecart_global = total_attendu_global - total_paye_global

    # Récupérer classes et sections existants dans eleves
    cursor.execute("SELECT DISTINCT classe FROM eleves")
    classes_disponibles = [row["classe"] for row in cursor.fetchall()]

    cursor.execute("""
        SELECT DISTINCT s.nom 
        FROM sections s
        JOIN classes c ON c.section_id = s.id
        JOIN eleves e ON e.classe = c.nom
    """)
    sections_disponibles = [row["nom"] for row in cursor.fetchall()]

    conn.close()

    return render_template(
        'statistiques_paiements.html',
        statistiques=statistiques,
        mois=mois,
        classe=classe,
        section=section,
        annee_scolaire=annee_scolaire,
        total_paye_global=total_paye_global,
        total_attendu_global=total_attendu_global,
        ecart_global=ecart_global,
        classes_disponibles=classes_disponibles,
        sections_disponibles=sections_disponibles
    )

@app.route('/telecharger_statistiques_paiements')
@login_required
def telecharger_statistiques_paiements():
    mois = request.args.get('mois', '')
    classe = request.args.get('classe', '')
    section = request.args.get('section', '')
    annee_scolaire = request.args.get('annee_scolaire', '')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = """
        SELECT 
            e.classe,
            s.nom AS section,
            %s AS mois,
            COUNT(DISTINCT e.matricule) AS nb_eleves,
            COUNT(DISTINCT p.matricule) AS nb_payeurs,
            COALESCE((
                SELECT SUM(p2.montant_paye)
                FROM paiements p2
                WHERE p2.matricule = e.matricule
                AND (%s = '' OR p2.mois = %s)
                AND (%s = '' OR p2.annee_scolaire = %s)
            ), 0) AS total_paye,
            COALESCE(t.montant * COUNT(DISTINCT e.matricule), 0) AS total_attendu
        FROM eleves e
        JOIN classes c ON e.classe = c.nom
        JOIN sections s ON c.section_id = s.id
        LEFT JOIN paiements p ON p.matricule = e.matricule 
            AND (%s = '' OR p.mois = %s) 
            AND (%s = '' OR p.annee_scolaire = %s)
        LEFT JOIN tarifs t ON t.classe_id = c.id AND t.type = 'minerval'
        WHERE (%s = '' OR e.classe = %s)
        AND (%s = '' OR s.nom = %s)
        GROUP BY e.classe, s.nom, t.montant
        ORDER BY e.classe
    """

    params = [
        mois,
        mois, mois,
        annee_scolaire, annee_scolaire,
        mois, mois,
        annee_scolaire, annee_scolaire,
        classe, classe,
        section, section
    ]

    cursor.execute(query, params)
    rows=cursor.fetchall()
    rows = [dict(row) for row in rows]  # convertit en dict modifiable
    if annee_scolaire and (mois == '' or mois is None):
        for row in rows:
            row["total_attendu"] *= 8

    conn.close()

    # Calcul des totaux globaux
    total_eleves = sum(row["nb_eleves"] for row in rows)
    total_payeurs = sum(row["nb_payeurs"] for row in rows)
    total_paye = sum(row["total_paye"] for row in rows)
    total_attendu = sum(row["total_attendu"] for row in rows)
    total_ecart = total_attendu - total_paye

    # Génération PDF
    filepath = os.path.join(DOSSIER_RECUS, "statistiques_paiements.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)

    largeur, hauteur = landscape(A4)
    styles = getSampleStyleSheet()

    data = [["N°", "Classe", "Section", "Mois", "Nbre élèves", "Ayant payé", "Total payé", "Total attendu", "Écart"]]
    for i, row in enumerate(rows, start=1):
        ecart = row["total_attendu"] - row["total_paye"]
        data.append([
            str(i),
            row["classe"],
            row["section"],
            row["mois"],
            str(row["nb_eleves"]),
            str(row["nb_payeurs"]),
            f"{row['total_paye']:,.1f} $",
            f"{row['total_attendu']:,.1f} $",
            f"{ecart:,.1f} $"
        ])

    # Ligne des totaux
    data.append([
        "",
        "TOTAL",
        "",
        "",
        str(total_eleves),
        str(total_payeurs),
        f"{total_paye:,.1f} $",
        f"{total_attendu:,.1f} $",
        f"{total_ecart:,.1f} $"
    ])

    table = Table(data, colWidths=[50, 200, 80, 70, 60, 60, 75, 75, 75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))

    def en_tete(canvas, doc):
        canvas.saveState()
        # 🔹 Images gauche et droite
        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 60, hauteur - 80, width=60, height=60, mask='auto')
            canvas.drawImage(logo_droit, largeur - 120, hauteur - 80, width=60, height=60, mask='auto')
        except:
            pass
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(largeur / 2, hauteur - 40, "COMPLEXE SCOLAIRE IMMACULEE CONCEPTION DE LA CHARITE")
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(largeur / 2, hauteur - 60, "STATISTIQUES DES PAIEMENTS")
        canvas.setFont("Helvetica", 12)
        canvas.drawString(60, hauteur - 100, f"Classe : {classe or '---'}")
        canvas.drawString(300, hauteur - 100, f"Section : {section or '---'}")
        canvas.drawString(440, hauteur - 100, f"Mois : {mois or '---'}")
        canvas.drawString(570, hauteur - 100, f"Année scolaire : {annee_scolaire or '---'}")
        canvas.drawRightString(largeur - 60, hauteur - 15, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.restoreState()

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), topMargin=120, leftMargin=25, rightMargin=25, bottomMargin=40)
    elements = [table]
    doc.build(elements, onFirstPage=en_tete, onLaterPages=en_tete)

    return send_file(filepath, as_attachment=False)

@app.route('/rapport_global_paiements', methods=['GET'])
@login_required
def rapport_global_paiements():
    mois = request.args.get('mois', '')
    classe = request.args.get('classe', '')
    section = request.args.get('section', '')
    annee_scolaire = request.args.get('annee_scolaire', '')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Récupérer les classes disponibles pour dropdown
    cursor.execute("SELECT DISTINCT classe FROM eleves")
    classes_disponibles = [row['classe'] for row in cursor.fetchall()]

    # Récupérer les sections disponibles pour dropdown
    cursor.execute("""
        SELECT DISTINCT s.nom 
        FROM sections s
        JOIN classes c ON c.section_id = s.id
        JOIN eleves e ON e.classe = c.nom
    """)
    sections_disponibles = [row['nom'] for row in cursor.fetchall()]

    # Récupération des élèves filtrés
    query_eleves = """
        SELECT e.matricule
        FROM eleves e
        JOIN classes c ON e.classe = c.nom
        JOIN sections s ON c.section_id = s.id
        WHERE (%s = '' OR e.classe = %s)
          AND (%s = '' OR s.nom = %s)
    """
    params_eleves = [classe, classe, section, section]
    cursor.execute(query_eleves, params_eleves)
    eleves=cursor.fetchall()
    matricules = [e['matricule'] for e in eleves]

    nb_total_eleves = len(matricules)

    # Préparer le filtre sur les matricules (éviter erreur SQL si liste vide)
    placeholders = ','.join(['%s'] * len(matricules)) if matricules else "'0'"

    # Total payé
    query_total_paye = f"""
        SELECT SUM(montant_paye) as total
        FROM paiements
        WHERE (%s = '' OR mois = %s)
          AND (%s = '' OR annee_scolaire = %s)
          AND matricule IN ({placeholders})
    """
    params_paye = [mois, mois, annee_scolaire, annee_scolaire] + matricules

    cursor.execute(query_total_paye, params_paye)
    total_paye=cursor.fetchone()['total'] or 0

    # Élèves ayant payé
    query_ayant_paye = f"""
        SELECT DISTINCT matricule
        FROM paiements
        WHERE (%s = '' OR mois = %s)
          AND (%s = '' OR annee_scolaire = %s)
          AND matricule IN ({placeholders})
    """
    params_ayant_paye = [mois, mois, annee_scolaire, annee_scolaire] + matricules
    
    cursor.execute(query_ayant_paye, params_ayant_paye)
    ayant_paye=cursor.fetchall()
    nb_ayant_paye = len(set([p['matricule'] for p in ayant_paye]))

    # Total attendu
    query_tarif = """
        SELECT t.montant, COUNT(DISTINCT e.matricule) as total_eleves
        FROM eleves e
        JOIN classes c ON e.classe = c.nom
        JOIN sections s ON c.section_id = s.id
        LEFT JOIN tarifs t ON t.classe_id = c.id AND t.type = 'minerval'
        WHERE (%s = '' OR e.classe = %s)
          AND (%s = '' OR s.nom = %s)
        GROUP BY t.montant
    """
    params_tarif = [classe, classe, section, section]
    total_attendu = 0
    nb_mois_par_annee = 8  # de Septembre à Avril

    cursor.execute(query_tarif, params_tarif)
    for ligne in cursor.fetchall():
        montant_par_eleve = ligne['montant'] or 0
        nombre_eleves = ligne['total_eleves'] or 0

        if mois == '':
            total_attendu += montant_par_eleve * nombre_eleves * nb_mois_par_annee
        else:
            total_attendu += montant_par_eleve * nombre_eleves

    conn.close()

    return render_template(
        'rapport_global_paiements.html',
        mois=mois,
        classe=classe,
        section=section,
        annee_scolaire=annee_scolaire,
        total_attendu=total_attendu,
        total_paye=total_paye,
        nb_ayant_paye=nb_ayant_paye,
        nb_total_eleves=nb_total_eleves,
        classes_disponibles=classes_disponibles,
        sections_disponibles=sections_disponibles,
        rapport_genere=True
    )


@app.route('/telecharger_rapport_global_paiements')
@login_required
def telecharger_rapport_global_paiements():
    mois = request.args.get('mois', '')
    classe = request.args.get('classe', '')
    section = request.args.get('section', '')
    annee_scolaire = request.args.get('annee_scolaire', '')
    print("Filtres reçus :", mois, classe, section, annee_scolaire)

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Obtenir tous les matricules filtrés
    query_eleves = """
        SELECT matricule FROM eleves
        WHERE (%s = '' OR classe = %s)
          AND (%s = '' OR section = %s)
    """
    cursor.execute(query_eleves, [classe, classe, section, section])
    eleves=cursor.fetchall()

    matricules = [e['matricule'] for e in eleves]
    nb_total_eleves = len(matricules)

    # Si aucun élève, éviter la suite
    if not matricules:
        total_paye = 0
        nb_ayant_paye = 0
    else:
        placeholders = ','.join('%s' for _ in matricules)

        # Total payé
        query_total_paye = f"""
            SELECT SUM(montant_paye) as total
            FROM paiements
            WHERE matricule IN ({placeholders})
              AND (%s = '' OR mois = %s)
              AND (%s = '' OR annee_scolaire = %s)
        """
        params_paye = matricules + [mois, mois, annee_scolaire, annee_scolaire]
        
        cursor.execute(query_total_paye, params_paye)
        total_paye=cursor.fetchone()['total'] or 0

        # Élèves ayant payé
        query_ayant_paye = f"""
            SELECT DISTINCT matricule FROM paiements
            WHERE matricule IN ({placeholders})
              AND (%s = '' OR mois = %s)
              AND (%s = '' OR annee_scolaire = %s)
        """
        params_ayant = matricules + [mois, mois, annee_scolaire, annee_scolaire]
      
        cursor.execute(query_ayant_paye, params_ayant)
        ayant_paye=cursor.fetchall()
        nb_ayant_paye = len(ayant_paye)

    # Total attendu
    query_tarif = """
    SELECT t.montant, COUNT(*) as total_eleves
    FROM eleves e
    LEFT JOIN classes c ON e.classe = c.nom
    LEFT JOIN tarifs t ON t.classe_id = c.id AND t.type = 'minerval'
    WHERE (%s = '' OR e.classe = %s)
      AND (%s = '' OR e.section = %s)
    GROUP BY t.montant
    """
    params_tarif = [classe, classe, section, section]

    total_attendu = 0
    cursor.execute(query_tarif, params_tarif)
    for ligne in cursor.fetchall():
        montant_par_eleve = ligne['montant'] or 0
        total_attendu += montant_par_eleve * ligne['total_eleves']
    if annee_scolaire and mois == '':
        total_attendu *= 8


    conn.close()

    # Génération PDF
    filepath = os.path.join(DOSSIER_RECUS, "rapports_global.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)

    styles = getSampleStyleSheet()
    largeur, hauteur = landscape(A4)

    def en_tete(canvas, doc):
        # 🔹 Images gauche et droite
        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 60, hauteur - 100, width=60, height=60, mask='auto')
            canvas.drawImage(logo_droit, largeur - 120, hauteur - 100, width=60, height=60, mask='auto')
        except:
            pass
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(largeur / 2, hauteur - 40, "COMPLEXE SCOLAIRE IMMACULEE CONCEPTION DE LA CHARITE")
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(largeur / 2, hauteur - 60, "RAPPORT GLOBAL DES PAIEMENTS")
        canvas.setFont("Helvetica", 12)
        canvas.drawString(60, hauteur - 120, f"Classe : {classe or '---'}")
        canvas.drawString(270, hauteur - 120, f"Section : {section or '---'}")
        canvas.drawString(410, hauteur - 120, f"Mois : {mois or '---'}")
        canvas.drawString(560, hauteur - 120, f"Année scolaire : {annee_scolaire or '---'}")
        canvas.setFont("Helvetica-Oblique", 10)
        canvas.drawRightString(largeur - 60, hauteur - 30, datetime.now().strftime("%d/%m/%Y %H:%M"))

    data = [
        ["Indicateur", "Valeur"],
        ["Total attendu", f"{total_attendu:,.1f} $"],
        ["Total payé", f"{total_paye:,.1f} $"],
        ["Écart", f"{(total_attendu - total_paye):,.1f} $"],
        ["Élèves ayant payé", f"{nb_ayant_paye} / {nb_total_eleves}"]
    ]

    table = Table(data, colWidths=[400, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), topMargin=140, leftMargin=30, rightMargin=30)
    doc.build([table], onFirstPage=en_tete, onLaterPages=en_tete)

    return send_file(filepath, as_attachment=False)

@app.route('/menu_frais_et_stock')
@login_required
def menu_frais_et_stock():
    log_action("Acces menu_frais_et_stock enregistré", session['nom_utilisateur'])
    return render_template('menu_frais_et_stock.html')

@app.route('/enregistrer_frais_etat', methods=['GET', 'POST'])
@login_required
def enregistrer_frais_etat():
    role = session.get('role_utilisateur', '')

    if role == 'lecture':
        return redirect(url_for('menu_frais_et_stock'))  # Ou vers une page où il peut juste consulter

    message = None
    if request.method == 'POST':
        matricule = request.form.get['matricule','Inconnu']
        tranche = request.form.get['tranche','Inconnu']
        montant = request.form.get['montant']
        date_paiement = request.form.get['date_paiement','Inconnu']
        caissier = session.get('nom_utilisateur', 'Inconnu')

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Récupérer section et annee_scolaire de l'élève
        cursor.execute("SELECT section, annee_scolaire FROM eleves WHERE matricule = %s", (matricule,))
        eleve_info = cursor.fetchone()

        if eleve_info:
            section = eleve_info['section']
            annee_scolaire = eleve_info['annee_scolaire']

            # 🔐 Vérification d'autorisation ici
            role_utilisateur = session.get('role_utilisateur', '').lower()
            if role_utilisateur not in ['full', section.lower()]:
                flash("Vous n'avez pas les droits pour effectuer cette action.", "danger")
                conn.close()
                return redirect(url_for('enregistrer_frais_etat'))
            # Vérifie si la même tranche a déjà été payée pour cette année scolaire
            cursor.execute("""
                SELECT 1 FROM frais_etat 
                WHERE matricule = %s AND tranche = %s AND annee_scolaire = %s
            """, (matricule, tranche, annee_scolaire))

            deja_paye = cursor.fetchone()
            if deja_paye:
                conn.close()
                flash(f"⚠️ L’élève {matricule} a déjà payé la {tranche} pour l’année scolaire {annee_scolaire}", "danger")
                return redirect(url_for("enregistrer_frais_etat"))

            # Insertion avec l'année scolaire
            cursor.execute("""
                INSERT INTO frais_etat (matricule, tranche, montant, date_paiement, caissier, annee_scolaire)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (matricule, tranche, montant, date_paiement, caissier, annee_scolaire))

            log_action("Paiement frais de l'etat enregistré", session['nom_utilisateur'])
            conn.commit()
            dernier_id = cursor.lastrowid  # ✅ Récupère l’ID de l’enregistrement

            conn.close()
            return redirect(url_for('recu_frais_etat', id=dernier_id))  # ✅ Redirige vers le reçu PDF

        else:
            conn.close()
            message = f"❌ Aucun élève trouvé avec le matricule {matricule}."

    return render_template("enregistrer_frais_etat.html", message=message, current_date=datetime.now().strftime('%Y-%m-%d'),)

@app.route('/recu_frais_etat/<int:id>')
@login_required
def recu_frais_etat(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Récupérer les infos du paiement
        cursor.execute("""
            SELECT f.*, e.nom, e.postnom, e.prenom
            FROM frais_etat f
            JOIN eleves e ON f.matricule = e.matricule
            WHERE f.id = %s
        """, (id,))
        frais = cursor.fetchone()

        conn.close()

        if not frais:
            return "❌ Paiement introuvable", 404

        nom_complet = f"{frais['nom']} {frais['postnom']} {frais['prenom']}"
        filepath = os.path.join(DOSSIER_RECUS, "recu_frais_etat.pdf")
        if not os.path.exists(DOSSIER_RECUS):
            os.makedirs(DOSSIER_RECUS)

        # Supprime l'ancien PDF si besoin
        if os.path.exists(filepath):
            os.remove(filepath)

        c = canvas.Canvas(filepath, pagesize=A6)

        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droite = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
                
            c.drawImage(logo_gauche, 15, 305, width=40, height=40, preserveAspectRatio=True, mask='auto')
            c.drawImage(logo_droite, 245, 305, width=40, height=40, preserveAspectRatio=True, mask='auto')
        except:
            pass
            # Filigrane
        #try:
            #logo = ImageReader("static/logo2.png")
            #c.saveState()
            #c.setFillAlpha(0.08)
            #c.drawImage(logo, 40, 100, width=240, height=240, preserveAspectRatio=True, mask='auto')
            #c.restoreState()
        #except:
                #pass

        # Texte
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(149, 320, "COMPLEXE SCOLAIRE")
        c.drawCentredString(149, 300, "IMMACULEE CONCEPTION")
        c.drawCentredString(149, 280, "DE LA CHARITE")
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(149, 260, "REÇU FRAIS DE L'ETAT")

        # Données
        c.setFont("Helvetica", 12)
        c.drawString(25, 240, f"Date : {frais['date_paiement']}")
        c.drawString(25, 220, f"Matricule : {frais['matricule']}")
        c.drawString(25, 200, f"Nom complet : {nom_complet}")
        c.drawString(25, 180, f"Tranche : {frais['tranche']}")
        montant=float(frais['montant'] or 0)
        c.drawString(25, 160, f"Montant payé : {montant:,.1f} FC")
        caissier = frais['caissier'] or "Inconnu"
        c.drawString(25, 140, f"Caissier : {caissier}")

        # Bas de page
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(25, 110, "Merci pour votre confiance!")
        c.drawString(25, 90, "Gardez bien votre reçu!")

        from reportlab.pdfbase import pdfdoc
        c._doc.Catalog.OpenAction = pdfdoc.PDFDictionary({
            "S": "/Named",
            "N": "/Print"
        })

        c.save()

        return send_file(filepath, as_attachment=False)

    except Exception as e:
        print("Erreur lors de la génération du reçu :", e)
        return "Une erreur s’est produite lors de la génération du reçu.", 500

@app.route('/afficher_recu_frais_etat/<int:id>')
@login_required
def afficher_recu_frais_etat(id):
    url_pdf = url_for('recu_frais_etat', id=id)
    return render_template('imprimer_pdf.html', url_pdf=url_pdf)

@app.route('/liste_frais_etat')
@login_required
def liste_frais_etat():
    matricule = request.args.get('matricule', '').strip()
    classe = request.args.get('classe', '').strip()
    section = request.args.get('section', '').strip()
    ordre = request.args.get('ordre', '').strip()  # "Oui" ou "Non"
    caissier = request.args.get('caissier', '').strip()
    tranche = request.args.get('tranche', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # On commence par récupérer tous les élèves avec leur total payé, tranche et caissier du dernier paiement
    # Cette requête rassemble l'élève avec la somme des paiements et les infos du dernier paiement (tranche et caissier)
    query = """
    SELECT 
        e.matricule, e.nom, e.postnom, e.prenom, e.genre, e.classe, e.section,
        IFNULL(SUM(f.montant), 0) AS total_paye,
        MAX(f.date_paiement) AS derniere_date,
        (SELECT f2.tranche FROM frais_etat f2 WHERE f2.matricule = e.matricule ORDER BY f2.date_paiement DESC LIMIT 1) AS tranche,
        (SELECT f3.caissier FROM frais_etat f3 WHERE f3.matricule = e.matricule ORDER BY f3.date_paiement DESC LIMIT 1) AS caissier
    FROM eleves e
    LEFT JOIN frais_etat f ON e.matricule = f.matricule
    WHERE 1=1
    """

    params = []

    # Filtres sur eleves
    if matricule:
        query += " AND e.matricule LIKE %s"
        params.append(f"%{matricule}%")
    if classe:
        query += " AND e.classe = %s"
        params.append(classe)
    if section:
        query += " AND e.section = %s"
        params.append(section)

    query += " GROUP BY e.matricule"

    # On appliquera les filtres tranche, caissier, ordre en Python après récupération car liés à frais_etat

    cursor.execute(query, params)
    eleves = cursor.fetchall()

    # Filtrage supplémentaire en Python
    eleves_filtres = []
    for eleve in eleves:
        # filtre tranche
        if tranche and (eleve['tranche'] != tranche):
            continue
        # filtre caissier
        if caissier and (eleve['caissier'] is None or caissier.lower() not in eleve['caissier'].lower()):
            continue
        # filtre ordre
        est_en_ordre = eleve['total_paye'] > 0
        if ordre:
            if ordre == 'Oui' and not est_en_ordre:
                continue
            if ordre == 'Non' and est_en_ordre:
                continue
        eleves_filtres.append(eleve)

    conn.close()

    # Récupérer toutes les classes et sections pour le filtre (optionnel, à adapter selon ta base)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT classe FROM eleves ORDER BY classe")
    classes = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT section FROM eleves ORDER BY section")
    sections = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template("liste_frais_etat.html",
                           eleves=eleves_filtres,
                           classes=classes,
                           sections=sections)

@app.route('/exporter_frais_etat_pdf')
@login_required
def exporter_frais_etat_pdf():
    matricule = request.args.get('matricule', '').strip()
    classe = request.args.get('classe', '').strip()
    section = request.args.get('section', '').strip()
    caissier = request.args.get('caissier', '').strip()
    tranche = request.args.get('tranche', '').strip()
    ordre = request.args.get('ordre', '').strip().lower()  # oui, non ou vide

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = """
        SELECT e.matricule, e.nom, e.postnom, e.prenom, e.genre, e.classe, e.section,
               f.tranche, f.montant, f.date_paiement, f.caissier
        FROM eleves e
        LEFT JOIN frais_etat f ON e.matricule = f.matricule
        WHERE 1=1
    """
    params = []

    if matricule:
        query += " AND e.matricule LIKE %s"
        params.append(f"%{matricule}%")
    if classe:
        query += " AND e.classe = %s"
        params.append(classe)
    if section:
        query += " AND e.section = %s"
        params.append(section)
    if tranche:
        query += " AND (f.tranche = %s OR f.tranche IS NULL)"
        params.append(tranche)
    if caissier:
        query += " AND (f.caissier LIKE %s OR f.caissier IS NULL)"
        params.append(f"%{caissier}%")

    if ordre == "oui":
        query += " AND f.montant IS NOT NULL AND f.montant > 0"
    elif ordre == "non":
        query += " AND (f.montant IS NULL OR f.montant = 0)"

    query += " ORDER BY e.nom, e.postnom, e.prenom"

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    if not results:
        return "Aucun élève trouvé selon les filtres.", 404

    # Création PDF
    filepath = os.path.join(DOSSIER_RECUS, "export_frais_etat.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)


    largeur, hauteur = landscape(A4)
    styles = getSampleStyleSheet()

    data = [
        ["N°", "Matricule", "Nom complet", "Genre", "Section", "Classe", "Tranche", "Montant (FC)", "Date", "Caissier"]
    ]

    total_montant = 0
    for i, row in enumerate(results, start=1):
        nom_complet = f"{row['nom']} {row['postnom']} {row['prenom']}"
        montant = row['montant'] if row['montant'] else 0
        total_montant += montant

        data.append([
            str(i),
            row['matricule'],
            Paragraph(nom_complet, styles["Normal"]),
            row['genre'],
            row['section'],
            Paragraph(row['classe'], styles["Normal"]),
            row['tranche'] if row['tranche'] else "—",
            f"{montant:,.1f}",
            row['date_paiement'] if row['date_paiement'] else "—",
            row['caissier'] if row['caissier'] else "—",
        ])

    table = Table(data, colWidths=[1.2*cm, 2.5*cm, 5*cm, 2*cm, 3*cm, 2.5*cm, 2*cm, 3*cm, 2*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    # Ligne total
    total_data = [["", "", "", "", "", "", "Montant total :", f"{total_montant:,.1f}", "", ""]]
    total_table = Table(total_data, colWidths=[1.2*cm, 2.5*cm, 5*cm, 2*cm, 3*cm, 2.5*cm, 2*cm, 3*cm, 2*cm, 2.5*cm])
    total_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (6, 0)),
        ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
        ("TEXTCOLOR", (6, 0), (7, 0), colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (6, 0), (7, 0), "RIGHT"),
    ]))

    def entete(canvas, doc):
        canvas.saveState()
        # 🔹 Images gauche et droite
        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 60, hauteur - 80, width=60, height=60, mask='auto')
            canvas.drawImage(logo_droit, largeur - 120, hauteur - 80, width=60, height=60, mask='auto')
        except:
            pass
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(largeur / 2, hauteur - 40, "COMPLEXE SCOLAIRE IMMACULÉE CONCEPTION DE LA CHARITÉ")
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(largeur / 2, hauteur - 60, "Liste des élèves - Frais de l'État")

        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(largeur - 60, hauteur - 15, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        canvas.setFont("Helvetica", 12)
        y = hauteur - 100
        canvas.drawString(60, y, f"Matricule : {matricule or ''}")
        canvas.drawString(180, y, f"Classe : {classe or ''}")
        canvas.drawString(380, y, f"Section : {section or ''}")
        canvas.drawString(510, y, f"Caissier : {caissier or ''}")
        canvas.drawString(650, y, f"Ordre : {ordre.capitalize() if ordre else ''}")
        canvas.restoreState()

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4),
                            topMargin=130, leftMargin=25, rightMargin=25, bottomMargin=40)
    elements = [table, Spacer(1, 12), total_table]
    doc.build(elements, onFirstPage=entete, onLaterPages=entete)
    filename = "export_frais_etat.pdf"
    return send_file(filepath, as_attachment=False, download_name=filename)

@app.route('/ajouter_achat_article', methods=['GET', 'POST'])
@login_required
def ajouter_achat_article():
    
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        matricule = request.form['matricule']
        code_article = request.form['code_article']
        quantite = int(request.form['quantite'])
        prix_unitaire = float(request.form['prix_unitaire'])
        total = quantite * prix_unitaire
        date_achat = request.form['date_achat']
        caissier = session.get('nom_utilisateur', 'Inconnu')
        cursor.execute("SELECT section FROM eleves WHERE matricule = %s", (matricule,))
        section_row = cursor.fetchone()
        if section_row:
            section = section_row['section']

                # 🔐 Vérification d'autorisation ici
            role_utilisateur = session.get('role_utilisateur', '').lower()
            if role_utilisateur not in ['full', section.lower()]:
                flash("Vous n'avez pas les droits pour effectuer cette action.", "danger")
                return redirect(url_for('ajouter_achat_article'))
        cursor.execute("""
            INSERT INTO achats_articles (matricule, code_article, quantite, prix_unitaire, total, date_achat, caissier)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (matricule, code_article, quantite, prix_unitaire, total, date_achat, caissier))
        log_action("Vente Articles enregistré", session['nom_utilisateur'])
        conn.commit()
        flash("Achat enregistré avec succès !", "success")

        conn.close()

        return redirect(url_for('ajouter_achat_article'))

    # Cas GET : on affiche le formulaire
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT code, nom, prix FROM articles")
    articles=cursor.fetchall()
    caissier_nom = session.get('nom_utilisateur', '')

    conn.close()

    return render_template("ajouter_achat_article.html",
                       articles=articles,
                       current_date=datetime.now().strftime('%Y-%m-%d'),
                       caissier_nom=caissier_nom)


@app.route('/historique_achats', methods=['GET'])
@login_required
def historique_achats():
    # Récupérer filtres depuis l'URL (GET)
    filtre_matricule = request.args.get('matricule', '').strip()
    filtre_section = request.args.get('section', '').strip()
    filtre_classe = request.args.get('classe', '').strip()
    filtre_caissier = request.args.get('caissier', '').strip()
    filtre_article = request.args.get('article', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Requête dynamique avec filtres
    query = """
        SELECT aa.*, e.nom, e.postnom, e.prenom, e.section, e.classe, a.nom AS nom_article
        FROM achats_articles aa
        JOIN eleves e ON aa.matricule = e.matricule
        JOIN articles a ON aa.code_article = a.code
        WHERE 1=1
    """
    params = []

    if filtre_matricule:
        query += " AND aa.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")
    if filtre_section:
        query += " AND e.section = %s"
        params.append(filtre_section)
    if filtre_classe:
        query += " AND e.classe = %s"
        params.append(filtre_classe)
    if filtre_caissier:
        query += " AND aa.caissier LIKE %s"
        params.append(f"%{filtre_caissier}%")
    if filtre_article:
        query += " AND a.nom LIKE %s"
        params.append(f"%{filtre_article}%")

    query += " ORDER BY aa.date_achat DESC"

    cursor.execute(query, params)
    achats=cursor.fetchall()

    # Pour les listes déroulantes de filtres, récupérer les valeurs uniques
    cursor.execute("SELECT DISTINCT section FROM eleves")
    sections = [row['section'] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT classe FROM eleves")
    classes = [row['classe'] for row in cursor.fetchall()]

    cursor.execute("SELECT code, nom FROM articles")
    articles = cursor.fetchall()  # liste de dicts

    conn.close()

    return render_template("historique_achats.html",
                           achats=achats,
                           sections=sections,
                           classes=classes,
                           articles=articles,
                           filtre_matricule=filtre_matricule,
                           filtre_section=filtre_section,
                           filtre_classe=filtre_classe,
                           filtre_caissier=filtre_caissier,
                           filtre_article=filtre_article)

@app.route('/exporter_historique_achats_pdf')
@login_required
def exporter_historique_achats_pdf():
    filtre_matricule = request.args.get('matricule', '').strip()
    filtre_section = request.args.get('section', '').strip()
    filtre_classe = request.args.get('classe', '').strip()
    filtre_caissier = request.args.get('caissier', '').strip()
    filtre_article = request.args.get('article', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = """
        SELECT aa.*, e.nom, e.postnom, e.prenom, e.section, e.classe, a.nom AS nom_article
        FROM achats_articles aa
        JOIN eleves e ON aa.matricule = e.matricule
        JOIN articles a ON aa.code_article = a.code
        WHERE 1=1
    """
    params = []

    if filtre_matricule:
        query += " AND aa.matricule LIKE %s"
        params.append(f"%{filtre_matricule}%")
    if filtre_section:
        query += " AND e.section = %s"
        params.append(filtre_section)
    if filtre_classe:
        query += " AND e.classe = %s"
        params.append(filtre_classe)
    if filtre_caissier:
        query += " AND aa.caissier LIKE %s"
        params.append(f"%{filtre_caissier}%")
    if filtre_article:
        query += " AND a.nom LIKE %s"
        params.append(f"%{filtre_article}%")

    query += " ORDER BY aa.date_achat DESC"

    
    cursor.execute(query, params)
    achats=cursor.fetchall()

    conn.close()

    if not achats:
        return "Aucun achat trouvé avec ces filtres.", 404

    # Préparation PDF
    filepath = os.path.join(DOSSIER_RECUS, "historique_achats.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)

    largeur, hauteur = landscape(A4)
    styles = getSampleStyleSheet()

    data = [
        ["N°", "Matricule", "Nom complet", "Section", "Classe", "Article",
         "Quantité", "Prix unitaire ($)", "Total ($)", "Date achat", "Caissier"]
    ]

    total_general = 0

    for i, achat in enumerate(achats, start=1):
        nom_complet = f"{achat['nom']} {achat['postnom']} {achat['prenom']}"
        total_general += float(achat.get('total', 0) or 0)


        data.append([
            str(i),
            achat['matricule'],
            Paragraph(nom_complet, styles["Normal"]),
            achat['section'],
            Paragraph(achat['classe'], styles["Normal"]),
            achat['nom_article'],
            str(achat['quantite']),
            f"{achat['prix_unitaire']:,.1f}",
            f"{achat['total']:,.1f}",
            achat['date_achat'],
            achat['caissier']
        ])

    data.append(["", "", "", "", "", "", "", "Total général :", f"{total_general:,.1f}", "", ""])

    table = Table(data, colWidths=[25, 70, 130, 50, 70, 80, 40, 70, 70, 70, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('BACKGROUND', (7, -1), (8, -1), colors.lightgrey),
        ('FONTNAME', (7, -1), (8, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (7, -1), (8, -1), 9),
        ('ALIGN', (7, -1), (8, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))

    # 🧠 Fonction d'entête dynamique avec filtres
    def header_with_filters(filtres):
        def inner(canvas, doc):
            canvas.saveState()
            # 🔹 Images gauche et droite
            try:
                logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
                logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
                canvas.drawImage(logo_gauche, 60, hauteur - 80, width=60, height=60, mask='auto')
                canvas.drawImage(logo_droit, largeur - 120, hauteur - 80, width=60, height=60, mask='auto')
            except:
                pass
            canvas.setFont("Helvetica-Bold", 16)
            canvas.drawCentredString(largeur / 2, hauteur - 40, "COMPLEXE SCOLAIRE IMMACULÉE CONCEPTION DE LA CHARITÉ")
            canvas.setFont("Helvetica-Bold", 14)
            canvas.drawCentredString(largeur / 2, hauteur - 60, "Historique des achats d'articles")
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(largeur - 60, hauteur - 15, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

            y = hauteur - 100
            canvas.setFont("Helvetica", 12)
            canvas.drawString(60, y, f"Matricule : {filtres['matricule'] or '---'}")
            canvas.drawString(180, y, f"Classe : {filtres['classe'] or '---'}")
            canvas.drawString(390, y, f"Section : {filtres['section'] or '---'}")
            canvas.drawString(520, y, f"Caissier : {filtres['caissier'] or '---'}")
            canvas.drawString(680, y, f"Article : {filtres['article'] or '---'}")
            canvas.restoreState()
        return inner

    filtres = {
        'matricule': filtre_matricule,
        'classe': filtre_classe,
        'section': filtre_section,
        'caissier': filtre_caissier,
        'article': filtre_article
    }

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), topMargin=120, leftMargin=25, rightMargin=25, bottomMargin=30)
    doc.build([table], onFirstPage=header_with_filters(filtres), onLaterPages=header_with_filters(filtres))

    return send_file(filepath, as_attachment=False)


@app.route('/parametres')
@login_required
def parametres():
    role_utilisateur = session.get('role_utilisateur', '').lower()

    if role_utilisateur != 'full':
        log_action("Acces parametres enregistré", session['nom_utilisateur'])
        return redirect(url_for('menu'))

    return render_template("parametres.html")

@app.route('/ajouter_article', methods=['GET', 'POST'])
@login_required
def ajouter_article():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        code = request.form['code']
        nom = request.form['nom']
        prix = request.form['prix']
        try:
            prix_float = float(prix)
        except ValueError:
            flash("Le prix doit être un nombre valide.", "danger")
            return redirect(url_for('ajouter_article'))

        # Enregistrement dans la base
        cursor.execute("INSERT INTO articles (code, nom, prix) VALUES (%s, %s, %s)", (code, nom, prix_float))
        conn.commit()
        log_action("Ajout article  enregistré", session['nom_utilisateur'])
    # Récupérer tous les articles pour affichage
    cursor.execute("SELECT * FROM articles ORDER BY id DESC")
    articles = cursor.fetchall()
    conn.close()

    return render_template("ajouter_article.html", articles=articles)

@app.route('/supprimer_article/<int:article_id>')
@login_required
def supprimer_article(article_id):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("DELETE FROM articles WHERE id = %s", (article_id,))
    log_action("suppression article enregistré", session['nom_utilisateur'])
    conn.commit()
    conn.close()
    return redirect(url_for('ajouter_article'))

@app.route('/parametres/classes', methods=['GET', 'POST'])
@login_required
def gerer_classes():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Récupérer toutes les sections pour le select
    cursor.execute("SELECT * FROM sections ORDER BY nom")
    sections = cursor.fetchall()

    if request.method == 'POST':
        nom_classe = request.form.get('nom_classe').strip()
        section_id = request.form.get('section_id')
        if nom_classe and section_id:
            # Vérifier doublon sur nom et section (optionnel)
            cursor.execute("SELECT id FROM classes WHERE nom = %s AND section_id = %s", (nom_classe, section_id))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO classes (nom, section_id) VALUES (%s, %s)", (nom_classe, section_id))
                conn.commit()

    # Récupérer classes avec nom de section jointe
    cursor.execute("""
        SELECT c.id, c.nom, s.nom AS section_nom
        FROM classes c
        LEFT JOIN sections s ON c.section_id = s.id
        ORDER BY c.nom
    """)
    log_action("Ajout classe  enregistré", session['nom_utilisateur'])
    classes = cursor.fetchall()
    conn.close()

    return render_template('parametres_classes.html', classes=classes, sections=sections)


@app.route('/parametres/classes/supprimer/<int:classe_id>')
@login_required
def supprimer_classe(classe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classes WHERE id = %s", (classe_id,))
    log_action("Suppression classe  enregistré", session['nom_utilisateur'])
    conn.commit()
    conn.close()
    return redirect(url_for('gerer_classes'))

from werkzeug.security import generate_password_hash

@app.route('/utilisateurs', methods=['GET', 'POST'])
@login_required
def utilisateurs():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        nom = request.form['nom'].strip()
        prenom = request.form['prenom'].strip()
        mot_de_passe = request.form['mot_de_passe'].strip()
        role = request.form['role']

        # Hachage du mot de passe
        mot_de_passe_hache = generate_password_hash(mot_de_passe, method="pbkdf2:sha256")

        cursor.execute("""
            INSERT INTO utilisateurs (nom, prenom, mot_de_passe, role)
            VALUES (%s, %s, %s, %s)
        """, (nom, prenom, mot_de_passe_hache, role))
        log_action("Ajout utilisateur enregistré", session['nom_utilisateur'])
        conn.commit()

    cursor.execute("SELECT * FROM utilisateurs ORDER BY nom")
    utilisateurs = cursor.fetchall()
    conn.close()
    return render_template("utilisateurs.html", utilisateurs=utilisateurs)


@app.route('/supprimer_utilisateur/<int:id>')
@login_required
def supprimer_utilisateur(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM utilisateurs WHERE id = %s", (id,))
    log_action("Suppression utilisateur  enregistré", session['nom_utilisateur'])
    conn.commit()
    conn.close()
    return redirect(url_for('utilisateurs'))


@app.route('/imprimer_pdf')
@login_required
def imprimer_pdf():
    url_pdf = request.args.get('url')
    if not url_pdf:
        return "URL du PDF manquante", 400

    url_pdf = unquote(url_pdf)  # pour décoder l'URL si elle est encodée
    return render_template('imprimer_pdf.html', url_pdf=url_pdf)


def get_eleve_by_matricule(matricule):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nom, postnom, prenom, genre, section, classe FROM eleves WHERE matricule = %s", (matricule,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'nom': row[0],
            'postnom': row[1],
            'prenom': row[2],
            'genre': row[3],
            'section': row[4],
            'classe': row[5]
        }
    return None

def get_situation_minerval(matricule, annee_scolaire):
    mois_list = ['Septembre', 'Octobre', 'Novembre', 'Décembre', 'Janvier', 'Février', 'Mars', 'Avril']
    situation = {}

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Récupérer la classe de l'élève
    cursor.execute("SELECT classe FROM eleves WHERE matricule = %s", (matricule,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return {mois: "Non payé" for mois in mois_list}  # Élève introuvable

    classe_nom = result[0]

    # 2. Trouver l'ID de la classe
    cursor.execute("SELECT id FROM classes WHERE nom = %s", (classe_nom,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return {mois: "Non payé" for mois in mois_list}  # Classe introuvable

    classe_id = result[0]

    # 3. Récupérer le tarif du minerval pour cette classe
    cursor.execute("SELECT montant FROM tarifs WHERE classe_id = %s AND type = 'minerval'", (classe_id,))
    result = cursor.fetchone()
    montant_a_payer = result[0] if result else 0

    # 4. Boucle sur les mois
    for mois in mois_list:
        cursor.execute("""
            SELECT SUM(montant_paye) 
            FROM paiements 
            WHERE matricule = %s AND mois = %s AND annee_scolaire = %s
        """, (matricule, mois, annee_scolaire))
        result = cursor.fetchone()
        total_paye = result[0] or 0

        # Comparaison intelligente
        if total_paye == 0:
            etat = "Non payé"
        elif total_paye < montant_a_payer:
            etat = "Paiement partiel"
        else:
            etat = "Payé"

        situation[mois] = etat

    conn.close()
    return situation

def get_situation_frais_etat(matricule, annee_scolaire):
    situation = {"Tranche 1": "Non payé", "Tranche 2": "Non payé"}

    conn = get_db_connection()
    cursor = conn.cursor()

    # Récupérer toutes les lignes payées (>0) pour cet élève et année scolaire
    cursor.execute("""
        SELECT tranche, montant FROM frais_etat
        WHERE matricule =  %s AND annee_scolaire = %s AND montant > 0
    """, (matricule, annee_scolaire))

    rows = cursor.fetchall()

    for tranche, montant in rows:
        if tranche in situation:
            situation[tranche] = "Payé"

    conn.close()
    return situation


@app.route('/situation_eleve', methods=['GET', 'POST'])
@login_required
def situation_eleve():
    situation = None
    eleve = None
    matricule = None
    annee_scolaire = None

    if request.method == 'POST':
        matricule = request.form['matricule']
        annee_scolaire = request.form['annee_scolaire']

        # Récupération infos élève
        eleve = get_eleve_by_matricule(matricule)

        if eleve:
            # Situation du minerval
            situation_minerval = get_situation_minerval(matricule, annee_scolaire)

            # Situation frais de l'état
            situation_frais_etat = get_situation_frais_etat(matricule, annee_scolaire)

            situation = {
                'minerval': situation_minerval,
                'etat': situation_frais_etat
            }

    return render_template('situation_eleve.html', eleve=eleve, situation=situation, annee_scolaire=annee_scolaire, matricule=matricule)


@app.route('/telecharger_situation_eleve/<matricule>/<annee_scolaire>')
@login_required
def telecharger_situation_eleve(matricule, annee_scolaire):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # ✅ Récupérer les infos de l'élève
  
    cursor.execute("SELECT * FROM eleves WHERE matricule = %s", (matricule,))
    eleve=cursor.fetchone()

    if not eleve:
        return "Élève introuvable", 404

    # ✅ Situation minerval
    mois_list = ["Septembre", "Octobre", "Novembre", "Décembre", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin"]
    situation_minerval = []
    for mois in mois_list:
        cursor.execute("""
            SELECT SUM(montant_paye) as total
            FROM paiements
            WHERE matricule = %s AND mois = %s AND annee_scolaire = %s
        """, (matricule, mois, annee_scolaire))
        total = cursor.fetchone()['total'] or 0

        cursor.execute("""
            SELECT montant
            FROM tarifs
            JOIN classes ON classes.id = tarifs.classe_id
            WHERE classes.nom = %s AND type = 'minerval'
        """, (eleve['classe'],))
        tarif = cursor.fetchone()
        montant_tarif = tarif['montant'] if tarif else 0

        if total >= montant_tarif:
            statut = "Payé"
        elif total > 0:
            statut = "Paiement partiel"
        else:
            statut = "Non payé"

        situation_minerval.append([mois, statut])

    # ✅ Situation frais de l'État
    situation_etat = [["Tranche", "Statut"]]
    for tranche in ["Tranche 1", "Tranche 2"]:
        cursor.execute("""
            SELECT montant FROM frais_etat
            WHERE matricule = %s AND tranche = %s AND annee_scolaire = %s
        """, (matricule, tranche, annee_scolaire))
        ligne = cursor.fetchone()
        montant = ligne['montant'] if ligne else 0
        statut = "Payé" if montant > 0 else "Non payé"
        situation_etat.append([tranche, statut])

    conn.close()

    # 📄 Génération PDF
    filepath = os.path.join(DOSSIER_RECUS, "situation_eleve.pdf")
    if not os.path.exists(DOSSIER_RECUS):
        os.makedirs(DOSSIER_RECUS)

    # Supprime l'ancien PDF si besoin
    if os.path.exists(filepath):
        os.remove(filepath)

    largeur, hauteur = landscape(A4)
    styles = getSampleStyleSheet()

    def en_tete(canvas, doc):
        try:
            logo_gauche = ImageReader(os.path.join(DOSSIER_STATIC,"logo1.jpg")) # ton logo à gauche
            logo_droit = ImageReader(os.path.join(DOSSIER_STATIC,"logo.jpg")) # ton logo à gauche
            canvas.drawImage(logo_gauche, 30, hauteur - 100, width=60, height=60)
            canvas.drawImage(logo_droit, largeur - 90, hauteur - 100, width=60, height=60)
        except:
            pass

        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(largeur / 2, hauteur - 40, "IMMACULEE CONCEPTION DE LA CHARITE")
        canvas.drawCentredString(largeur / 2, hauteur - 60, "SITUATION DE L'ÉLÈVE")
        canvas.setFont("Helvetica", 12)
        canvas.drawString(30, hauteur - 120, f"Nom : {eleve['nom']} {eleve['postnom']} {eleve['prenom']}")
        canvas.drawString(320, hauteur - 120, f"Matricule : {matricule}")
        canvas.drawString(30, hauteur - 140, f"Classe : {eleve['classe']} - Section : {eleve['section']}")
        canvas.drawString(420, hauteur - 140, f"Année scolaire : {annee_scolaire}")
        canvas.setFont("Helvetica-Oblique", 9)
        canvas.drawRightString(largeur - 30, hauteur - 30, datetime.now().strftime('%d/%m/%Y %H:%M'))

    # Tableaux
    table_minerval = Table([["Mois", "Situation"]] + situation_minerval, colWidths=[200, 200])
    table_minerval.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    table_etat = Table(situation_etat, colWidths=[200, 200])
    table_etat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#006400")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))

    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), topMargin=160, leftMargin=30, rightMargin=30)
    doc.build([table_minerval, Spacer(1, 20), table_etat], onFirstPage=en_tete, onLaterPages=en_tete)

    return send_file(filepath, as_attachment=False)

#Point d'entree principal
if __name__ == '__main__':
    app.run(debug=True, port=5002)