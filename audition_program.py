# Script to assign dancers to pieces for auditions
# Author: Sandy Jiang w/ file reading/writing stuff by Karin Tsai

PRINTOUT_PATH = 'piece_assignments/'
MAPS_PATH = 'maps/'

CHOREO_PREF_FILE = 'CHOREO_SPRING2015.csv'
CHOREO_PREF_HEADERS = ['id', 'name', 'total', 'male', 'female']

DANCER_PREF_FILE = 'DANCER_SPRING_2015.csv'
DANCER_PREF_HEADERS = ['date', 'first', 'last', 'id', 'gender', 'num_pieces']
DANCER_PREF_ENDING_COLUMNS = ['agreement']

SIGN_IN_FILE = 'SIGN_IN_SPRING2015.csv'
SIGN_IN_HEADERS = ['date', 'id', 'last', 'first', 'class_year', 'email',
                   'college', 'semesters', 'phone']


class Dancer(object):
    def __init__(self, _id, first_name, last_name, gender, num_pieces, email,
                 piece_rankings, phone):
        self.id = _id
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.num_pieces = num_pieces
        self.email = email
        self.phone = phone
        self.piece_rankings = piece_rankings
        self.piece_ids = []

    def __repr__(self):
        return "%d %s %s (%s, %s)" % (self.id, self.first_name, self.last_name, 
                                      self.email, self.phone)

    def done(self):
        return self.num_pieces == 0

    def match(self, piece, dancer_map, alternates=0):
        return ((not self.done()) and (not piece.full()) and 
                (piece.genderOk(self, dancer_map)) and
                (self.id in piece.dancer_rankings[0:piece.capacity+alternates]) and 
                (piece.id in self.piece_rankings[0:self.num_pieces]))

    def noChance(self, piece):
        #dancer has no chance of getting into the piece: full or didn't rank the dancer
        return (self not in piece.dancers and (piece.full() or 
                self.id not in piece.dancer_rankings))

class Piece(object):
    def __init__(self, _id, name, capacity,dancer_rankings, gender_constraints):
        self.id = _id
        self.name = name
        self.capacity = capacity
        self.gender_constraints = gender_constraints
        self.dancer_rankings = dancer_rankings
        self.dancers = []

    def __repr__(self):
        return "Piece(%r, %r)" % (self.id, self.name)

    def assign(self, dancer):
        self.dancers.append(dancer)
        dancer.piece_ids.append(self)
        dancer.piece_rankings.remove(self.id) #remove piece from dancer's ranking list
        dancer.num_pieces -= 1

    def full(self):
        return len(self.dancers) >= self.capacity

    def genderOk(self, curr_dancer, dancer_map):
        if not self.gender_constraints: return True
        else:
            num_of_gender = 0
            for dancer in self.dancers:
                if dancer.gender == curr_dancer.gender:
                    num_of_gender += 1
            return num_of_gender < (self.gender_constraints[curr_dancer.gender]).max
    
    def noChance(self, dancer):
        #piece not in dancer rankings should never happen because checked previously
        #dancer will never get into piece: didn't rank or is already done. remove from rankings
        return (dancer not in self.dancers and (self.id not in dancer.piece_rankings or 
                dancer.done()))

class GenderConstraint(object):
    def __init__(self, _min, _max):
        self.min = _min
        self.max = _max

def _csv_to_dancers():
    """
    create map of dancer_id to dancer objects

    NOTE: this does not error check because it assumes error checking already
          happened while running print_audition_sheets.py
    """
    dancer_signin_file = open(SIGN_IN_FILE, 'rU')
    contact_map = {}
    for i, line in enumerate(dancer_signin_file):
        if i == 0: # header line
            continue

        columns = line.strip().split(',')
        _id = int(columns[SIGN_IN_HEADERS.index('id')])
        email = columns[SIGN_IN_HEADERS.index('email')]
        phone = columns[SIGN_IN_HEADERS.index('phone')]
        contact_map[_id] = (email, phone)
    dancer_signin_file.close()

    dancer_ranking_file = open(DANCER_PREF_FILE, 'rU')
    dancer_map = {}
    for i, line in enumerate(dancer_ranking_file):
        if i == 0: # header line
            continue

        columns = line.strip().split(',')
        _id = int(columns[DANCER_PREF_HEADERS.index('id')])
        first_name = columns[DANCER_PREF_HEADERS.index('first')]
        last_name = columns[DANCER_PREF_HEADERS.index('last')]
        gender = columns[DANCER_PREF_HEADERS.index('gender')]
        num_pieces = int(columns[DANCER_PREF_HEADERS.index('num_pieces')])
        preferences = columns[len(DANCER_PREF_HEADERS):-len(DANCER_PREF_ENDING_COLUMNS)]
        ranking_tuples = [(dance_index, ranking) for dance_index, ranking
                          in enumerate(preferences) if ranking]
        sorted_ranking_tuples = sorted(ranking_tuples,
                                       key=lambda (dance_index, ranking): int(ranking))
        piece_rankings = [dance_index+1 for (dance_index, ranking) in sorted_ranking_tuples]
        (email, phone) = contact_map.get(_id, ('no email', 'no phone'))

        dancer_map[_id] = Dancer(_id, first_name, last_name, gender, num_pieces,
                                 email, piece_rankings, phone)

    dancer_ranking_file.close()
    return dancer_map

def _csv_to_pieces():
    choreo_ranking_file = open(CHOREO_PREF_FILE, 'rU')
    piece_map = {}
    for i, line in enumerate(choreo_ranking_file):
        if i == 0: # header line
            continue

        columns = line.strip().split(',')
        _id = int(columns[CHOREO_PREF_HEADERS.index('id')])
        name = columns[CHOREO_PREF_HEADERS.index('name')]
        total = int(columns[CHOREO_PREF_HEADERS.index('total')])
        male = int(columns[CHOREO_PREF_HEADERS.index('male')])
        female = int(columns[CHOREO_PREF_HEADERS.index('female')])
        preferences = columns[len(CHOREO_PREF_HEADERS):]
        dancer_rankings = [int(p) for p in preferences if p]

        gender_constraints = {}
        if male + female == total:
            gender_constraints['F'] = GenderConstraint(female, female)
            gender_constraints['M'] = GenderConstraint(male, male)


        piece_map[_id] = Piece(_id, name, total, dancer_rankings, gender_constraints)

    choreo_ranking_file.close()
    return piece_map

def assignDefinites(piece_map, dancer_map):
    for piece in piece_map.values():
        for dancer_id in piece.dancer_rankings[0:piece.capacity]: #only definites
            dancer = dancer_map[dancer_id]
            if piece.noChance(dancer):
                piece.dancer_rankings.remove(dancer.id)
                continue
            if dancer.match(piece, dancer_map):
                piece.assign(dancer)

def assignRest(piece_map, dancer_map, alternates):
    for piece in piece_map.values():
        if piece.full(): continue
        for dancer_id in piece.dancer_rankings[0:piece.capacity+alternates]:  
            dancer = dancer_map[dancer_id]
            if dancer.id not in piece.dancer_rankings: continue
            if dancer in piece.dancers: continue #already in the piece
            if piece.noChance(dancer):
                piece.dancer_rankings.remove(dancer.id)
                continue
            if dancer.match(piece, dancer_map, alternates):
                piece.assign(dancer)
                continue
            else:
                #if the piece is not in dancer's top pieces, go through the pieces before
                rank = dancer.piece_rankings.index(piece.id) 
                for otherPiece_id in dancer.piece_rankings[0:rank]:
                    otherPiece = piece_map[otherPiece_id]
                    checkOtherPiece(piece_map, dancer_map, alternates, dancer, otherPiece, piece)
                    if dancer.match(piece, dancer_map, alternates):
                        piece.assign(dancer)

def checkOtherPiece(piece_map, dancer_map, alternates, dancer, otherPiece, piece):
    if dancer.noChance(otherPiece):
        dancer.piece_rankings.remove(otherPiece.id)
        if dancer.match(piece, dancer_map, alternates):
            piece.assign(dancer)
        return
    elif dancer.id in otherPiece.dancer_rankings:
        if dancer.match(otherPiece, dancer_map):
            otherPiece.assign(dancer)
        else:
            #dancer is ranked (alternate), check dancers before
            rank = otherPiece.dancer_rankings.index(dancer.id)
            for otherDancer_id in otherPiece.dancer_rankings[0:rank]:
                otherDancer = dancer_map[otherDancer_id]
                if otherDancer.id in otherPiece.dancer_rankings:
                    checkOtherDancer(piece_map, dancer_map, alternates, dancer, otherDancer, otherPiece)
        return

def checkOtherDancer(piece_map, dancer_map, alternates, dancer, otherDancer, piece):
    if piece.noChance(otherDancer):
        piece.dancer_rankings.remove(otherDancer.id)
        if dancer.match(piece, dancer_map, alternates):
            piece.assign(dancer)
        return
    elif piece in otherDancer.piece_rankings:
        if otherDancer.match(piece, dancer_map):
            piece.assign(otherDancer)
        else:
            #piece is ranked in other dancer's list, but not in top
            rank = otherDancer.piece_rankings.index(piece.id) 
            for otherPiece_id in otherDancer.piece_rankings[0:rank]:
                otherPiece = piece_map[otherPiece_id]
                checkOtherPiece(piece_map, dancer_map, alternates, otherDancer, otherPiece, piece)
        return

def print_txts(piece_map, dancer_map):
    #assigned text files
    for piece in piece_map.values():
        f = open(PRINTOUT_PATH + '%s - %s.txt' % (piece.id, piece.name.replace('/', '_')), 'w+')
        print >> f, '********************'
        print >> f, '%s (%s)' % (piece.name, piece.id)
        if piece.gender_constraints:
            gender_constraint_string = ', '.join([str(gc) for gc in piece.gender_constraints])
        else:
            gender_constraint_string = 'no gender constraints'
        print >> f, 'Desired: %d dancers (%s)' % (piece.capacity, gender_constraint_string)
        print >> f, 'Matched: %d dancers (%d female, %d male)' % (len(piece.dancers),
                                                                  len([d for d in piece.dancers
                                                                       if d.gender == 'F']),
                                                                  len([d for d in piece.dancers
                                                                       if d.gender == 'M']))
        print >> f, '********************'
        sorted_dancers = sorted(piece.dancers, key=lambda d: d.id)
        for dancer in sorted_dancers:
            print >> f, dancer
        print >> f, '********************'
        print >> f, 'Emails to copy:'
        print >> f, ', '.join([d.email for d in piece.dancers])
        print >> f, '********************'
        print >> f, 'List of names:'
        for dancer in sorted_dancers:
            print >> f, "%s" % (dancer.first_name + " " + dancer.last_name)

        f.close()

    #unassigned text file
    f = open(PRINTOUT_PATH + 'unassigned.txt', 'w+')
    unassigned = []
    for dancer in dancer_map.values():
        if not dancer.piece_ids and dancer.num_pieces:
            unassigned.append(dancer)
            print >> f, '%d\t%s\t%s\t%s\t%s' % (dancer.id,
                                                dancer.first_name + " " + dancer.last_name,
                                                dancer.gender,
                                                dancer.email,
                                                dancer.phone)
    print >> f, '********************'
    print >> f, 'Emails to copy:'
    print >> f, ', '.join([d.email for d in unassigned]) 
    f.close()
    
def run():
    dancer_map = _csv_to_dancers()
    piece_map = _csv_to_pieces()

    assignDefinites(piece_map, dancer_map)
        
    #Handpicked matches (due to executive decisions during the manual selection process)
    """
    piece_map[3].assign(dancer_map[199])
    piece_map[17].assign(dancer_map[200])
    piece_map[16].assign(dancer_map[254])
    piece_map[19].assign(dancer_map[206])
    """
    
    for i in xrange(0,100):
        alternates = 0
        if i > 10:
            alternates = (i//4)+1 #increase # of alternates every four turns
        assignRest(piece_map, dancer_map, alternates)
    print_txts(piece_map, dancer_map)

    print "Done!"
    
run()
